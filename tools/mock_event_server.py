"""
Sahte XProtect Event Server.

XProtect erisimi olmadan gelistirme yapmak icin 9090'i dinler ve gelen
analytics event XML'ini terminale basar.

Kullanim:
    python tools/mock_event_server.py

config.yaml icinde:
    event_server: "127.0.0.1"
"""

import socketserver
import sys
from datetime import datetime

PORT = 9090


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        data = b""
        self.request.settimeout(2.0)
        try:
            while True:
                chunk = self.request.recv(4096)
                if not chunk:
                    break
                data += chunk
        except OSError:
            pass

        text = data.decode("utf-8", errors="replace")
        stamp = datetime.now().strftime("%H:%M:%S")

        event_type = extract(text, "<Type>", "</Type>") or "?"
        message = extract(text, "<Message>", "</Message>") or ""
        source = extract(text, "<Name>", "</Name>") or "?"

        if event_type == "Analytics Heartbeat":
            print(f"[{stamp}] heartbeat  ({source})")
        else:
            print(f"\n[{stamp}] ===== OLAY =====")
            print(f"  Tip     : {event_type}")
            print(f"  Kaynak  : {source}")
            print(f"  Mesaj   : {message}")
            print(f"  Aciklama: {extract(text, '<Description>', '</Description>') or ''}")
            print("  " + "-" * 40)

        try:
            self.request.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n")
        except OSError:
            pass


def extract(text, start_tag, end_tag):
    start = text.find(start_tag)
    if start == -1:
        return None
    start += len(start_tag)
    end = text.find(end_tag, start)
    return text[start:end].strip() if end != -1 else None


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    print(f"Sahte Event Server dinliyor: 0.0.0.0:{PORT}")
    print("config.yaml icinde event_server: 127.0.0.1 olmali.")
    print("Cikis: Ctrl+C\n")
    try:
        with Server(("0.0.0.0", PORT), Handler) as server:
            server.serve_forever()
    except KeyboardInterrupt:
        print("\nDurduruldu.")
        sys.exit(0)
