"""
XProtect Analytics Event test scripti.

Amac: detection'a hic dokunmadan, olay borusunun calistigini dogrulamak.
Basarili olursa Smart Client > Alarm Manager'da alarm satiri gorunur.

Kullanim:
    python tools/test_event.py
    python tools/test_event.py "Fire Detected"
"""

import os
import socket
import sys
import uuid
from datetime import datetime

import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.yaml")

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


def build_event(event_type, message, source, description=""):
    return XML_TEMPLATE.format(
        event_id=str(uuid.uuid4()),
        timestamp=datetime.now().astimezone().isoformat(),
        event_type=event_type,
        message=message,
        description=description,
        source=source,
    )


def send_event(xml, host, port, timeout=5.0):
    body = xml.encode("utf-8")
    request = (
        b"POST / HTTP/1.1\r\n"
        b"Content-Type: text/xml\r\n"
        b"Content-Length: " + str(len(body)).encode() + b"\r\n"
        b"Connection: Close\r\n"
        b"\r\n" + body
    )
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.sendall(request)
            try:
                response = sock.recv(1024)
            except socket.timeout:
                response = b""
        return True, response.decode("utf-8", errors="replace")
    except OSError as exc:
        return False, str(exc)


if __name__ == "__main__":
    if not os.path.exists(CONFIG_PATH):
        print("config.yaml bulunamadi. config.example.yaml dosyasini kopyala.")
        sys.exit(1)

    with open(CONFIG_PATH, encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle)

    event_type = sys.argv[1] if len(sys.argv) > 1 else "Smoke Detected"
    host, port, source = cfg["event_server"], cfg["event_port"], cfg["source_name"]

    xml = build_event(
        event_type=event_type,
        message=f"TEST - {event_type} (guven 0.91)",
        source=source,
        description="test_event.py tarafindan gonderildi",
    )

    print(f"-> {host}:{port}")
    print(f"   Tip    : {event_type}")
    print(f"   Kaynak : {source}\n")

    ok, detail = send_event(xml, host, port)

    if ok:
        print("BAGLANTI OK. Simdi kontrol et:")
        print("  1. Smart Client > Alarm Manager'da alarm gorunuyor mu?")
        print("  2. Gorunmuyorsa Management Client > Rules and Events > Analytics")
        print(f"     Events altinda '{event_type}' tanimli mi?")
        print("  3. Alarm var ama kameraya bagli degilse source_name degeri")
        print("     XProtect'teki kamera adiyla birebir eslesmiyor demektir.")
        if detail.strip():
            print(f"\n  Sunucu yaniti: {detail.strip()[:200]}")
    else:
        print(f"BAGLANTI HATASI: {detail}")
        print("\nKontrol listesi (docs/analytics-event-protocol.md):")
        print("  - Event Server calisiyor mu?")
        print("  - Options > Analytics Events > Enabled isaretli mi?")
        print("  - Bu makinenin IP'si 'events allowed from' listesinde mi?")
        print("  - Ayar degistikten sonra Event Server yeniden baslatildi mi?")
        print("  - Windows Firewall 9090 portunu aciyor mu?")
