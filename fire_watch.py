"""
Milestone XProtect yangin/duman tespit servisi.

RTSP'den kare alir, hazir egitilmis YOLOv8 modeliyle duman/ates tespiti
yapar, zamansal dogrulamadan gecirir ve XProtect Event Server'a analytics
event olarak gonderir. Tek proses, tek dosya - SPEC.md ve CLAUDE.md'deki
kisitlara bakmadan buraya yeni bagimlilik veya sinif ekleme.
"""

import argparse
import os
import socket
import sys
import time
import uuid
from collections import deque
from datetime import datetime

import cv2
import yaml
from ultralytics import YOLO

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")

XML_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<AnalyticsEvent xmlns:i="http://www.w3.org/2001/XMLSchema-instance" xmlns="urn:milestone-systems">
  <EventHeader>
    <ID>{event_id}</ID>
    <Timestamp>{timestamp}</Timestamp>
    <Type>{event_type}</Type>
    <Message>{message}</Message>
    <Source>
      <Name>{source}</Name>
    </Source>
  </EventHeader>
  <Description>{description}</Description>
</AnalyticsEvent>"""


def log(msg):
    stamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{stamp}] {msg}", flush=True)


class EventSender:
    """XProtect Event Server'a analytics event gonderir.

    Gonderim hatasi uygulamayi durdurmaz - sadece loglanir. Yeniden deneme
    dongusu kurulmaz, bir sonraki pozitif kare zaten yeni olay uretir.
    """

    def __init__(self, host, port, source_name, dry_run=False, timeout=5.0):
        self.host = host
        self.port = port
        self.source_name = source_name
        self.dry_run = dry_run
        self.timeout = timeout

    def _build_xml(self, event_type, message, description):
        return XML_TEMPLATE.format(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now().astimezone().isoformat(),
            event_type=event_type,
            message=message,
            description=description,
            source=self.source_name,
        )

    def send(self, event_type, message, description=""):
        xml = self._build_xml(event_type, message, description)

        if self.dry_run:
            log(f"[DRY-RUN] {event_type}: {message}")
            return

        body = xml.encode("utf-8")
        request = (
            b"POST / HTTP/1.1\r\n"
            b"Content-Type: text/xml\r\n"
            b"Content-Length: " + str(len(body)).encode() + b"\r\n"
            b"Connection: Close\r\n"
            b"\r\n" + body
        )
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
                sock.sendall(request)
        except OSError as exc:
            log(f"HATA: olay gonderilemedi ({event_type}): {exc}")
            return

        log(f"olay gonderildi: {event_type} - {message}")


class FrameSource:
    """RTSP veya dosyadan kare okur. Baglanti kopunca yeniden dener."""

    def __init__(self, source, target_fps=4.0, reconnect_wait=3.0):
        self.source = source
        self.target_fps = target_fps
        self.reconnect_wait = reconnect_wait
        self.cap = None
        self._open()

    def _open(self):
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            log(f"HATA: kaynak acilamadi: {self.source}")

    def frames(self):
        frame_interval = 1.0 / self.target_fps
        last_grab = 0.0

        while True:
            if self.cap is None or not self.cap.isOpened():
                log(f"kaynaga baglaniliyor: {self.source}")
                self._open()
                if self.cap is None or not self.cap.isOpened():
                    time.sleep(self.reconnect_wait)
                    continue

            # RTSP buffer birikimini onlemek icin grab() ile en guncel kareye atla
            ok = self.cap.grab()
            if not ok:
                log("kare alinamadi, yeniden baglaniliyor")
                self.cap.release()
                self.cap = None
                time.sleep(self.reconnect_wait)
                continue

            now = time.monotonic()
            if now - last_grab < frame_interval:
                continue
            last_grab = now

            ok, frame = self.cap.retrieve()
            if not ok or frame is None:
                continue

            yield frame

    def release(self):
        if self.cap is not None:
            self.cap.release()


class Detector:
    """Hazir egitilmis YOLOv8 modeliyle kare basina duman/ates tespiti yapar."""

    def __init__(self, model_path, conf_threshold, fire_labels, smoke_labels):
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        self.fire_labels = {label.lower() for label in fire_labels}
        self.smoke_labels = {label.lower() for label in smoke_labels}

        names = self.model.names
        log(f"model yuklendi: {model_path}")
        log(f"model sinif isimleri: {list(names.values())}")

    def detect(self, frame):
        """Karede en yuksek guvenli fire/smoke tespitini dondurur.

        Donus: (kind, confidence) ya da (None, 0.0). kind "fire" ya da "smoke".
        """
        results = self.model.predict(frame, verbose=False)
        best_kind, best_conf = None, 0.0

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            for box in boxes:
                conf = float(box.conf[0])
                if conf < self.conf_threshold:
                    continue
                label = self.model.names[int(box.cls[0])].lower()

                if label in self.fire_labels:
                    kind = "fire"
                elif label in self.smoke_labels:
                    kind = "smoke"
                else:
                    continue

                if conf > best_conf:
                    best_kind, best_conf = kind, conf

        return best_kind, best_conf


class Confirmer:
    """Zamansal dogrulama: kayan pencere + cooldown.

    Tek karelik pozitifi olaya cevirmek yasak - bu sinif kaldirilamaz.
    Fire ve smoke icin ayri pencere ve cooldown tutulur, birbirini
    engellemesinler diye.
    """

    def __init__(self, window, min_hits, cooldown_sec):
        self.window = window
        self.min_hits = min_hits
        self.cooldown_sec = cooldown_sec
        self.history = {"fire": deque(maxlen=window), "smoke": deque(maxlen=window)}
        self.last_alarm_at = {"fire": 0.0, "smoke": 0.0}

    def update(self, kind):
        """En son tespiti kaydeder, alarm uretilmeli mi karar verir.

        `kind` None olabilir (bu karede tespit yok). Donus: alarma neden
        olan kind ("fire"/"smoke") ya da None.
        """
        now = time.monotonic()

        for k in ("fire", "smoke"):
            self.history[k].append(1 if k == kind else 0)

        for k in ("fire", "smoke"):
            hits = sum(self.history[k])
            if hits < self.min_hits:
                continue
            if now - self.last_alarm_at[k] < self.cooldown_sec:
                continue
            self.last_alarm_at[k] = now
            return k, hits

        return None, 0


EVENT_TYPE = {"fire": "Fire Detected", "smoke": "Smoke Detected"}


def run(config, source_override=None, show=False, dry_run=False):
    sender = EventSender(
        host=config["event_server"],
        port=config["event_port"],
        source_name=config["source_name"],
        dry_run=dry_run,
    )

    detector = Detector(
        model_path=config["model_path"],
        conf_threshold=config["conf_threshold"],
        fire_labels=config["fire_labels"],
        smoke_labels=config["smoke_labels"],
    )

    confirmer = Confirmer(
        window=config["window"],
        min_hits=config["min_hits"],
        cooldown_sec=config["cooldown_sec"],
    )

    source = source_override or config["rtsp_url"]
    frame_source = FrameSource(source, target_fps=config["target_fps"])

    heartbeat_sec = config["heartbeat_sec"]
    last_heartbeat = 0.0

    log(f"servis basladi - kaynak: {source}")

    try:
        for frame in frame_source.frames():
            now = time.monotonic()

            if now - last_heartbeat >= heartbeat_sec:
                sender.send("Analytics Heartbeat", "servis calisiyor")
                last_heartbeat = now

            kind, conf = detector.detect(frame)
            alarm_kind, hits = confirmer.update(kind)

            if show:
                label = f"{kind} ({conf:.2f})" if kind else "-"
                text = f"tespit: {label}  pencere: fire={sum(confirmer.history['fire'])} smoke={sum(confirmer.history['smoke'])}"
                cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.imshow("fire_watch", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            if alarm_kind:
                event_type = EVENT_TYPE[alarm_kind]
                message = f"{event_type} - guven {conf:.2f}"
                description = f"{hits}/{confirmer.window} kare pozitif"
                sender.send(event_type, message, description)

    except KeyboardInterrupt:
        log("durduruldu (Ctrl+C)")
    finally:
        frame_source.release()
        if show:
            cv2.destroyAllWindows()


def load_config():
    if not os.path.exists(CONFIG_PATH):
        print("config.yaml bulunamadi. config.example.yaml dosyasini kopyala.")
        sys.exit(1)
    with open(CONFIG_PATH, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def parse_args():
    parser = argparse.ArgumentParser(description="Milestone yangin/duman tespit servisi")
    parser.add_argument("--source", help="RTSP url veya video dosyasi (config'i ezer)")
    parser.add_argument("--show", action="store_true", help="Goruntuyu pencerede goster")
    parser.add_argument("--dry-run", action="store_true", help="Olay gonderme, sadece logla")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    cfg = load_config()
    run(cfg, source_override=args.source, show=args.show, dry_run=args.dry_run)
