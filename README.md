# Milestone yangin/duman tespiti

XProtect kameralarindan RTSP ile goruntu alir, duman/ates tespit eder, sonucu
XProtect'e analytics event olarak geri gonderir. Alarm XProtect'in kendi Alarm
Manager'inda gorunur.

## Kurulum

Bagimliliklar (`opencv-python`, `ultralytics`) buyuk ve sik degisiyor - repoya
girmezler, `.gitignore` bunlari (`.venv/`, `*.pt`, `*.onnx`, `config.yaml`)
disarida tutar. Her gelistirme ortaminda asagidaki adimlar tekrarlanmali.

macOS sistem Python'u `pip install`'a dogrudan izin vermez (PEP 668,
"externally-managed-environment" hatasi), bu yuzden sanal ortam sart:

```bash
python3 -m venv .venv
source .venv/bin/activate       # her yeni terminalde tekrar calistir
pip install -r requirements.txt
cp config.example.yaml config.yaml
```

`config.yaml` icindeki `event_server`, `source_name` ve `rtsp_url` degerlerini doldur.

Model dosyasi: Roboflow Universe veya Hugging Face uzerinden hazir egitilmis bir
YOLOv8 fire/smoke agirligi indir, `fire_smoke.pt` olarak dizine koy.

> `ultralytics` (PyTorch dahil) birkac GB yer kaplar. Kurulum sirasinda
> "No space left on device" hatasi alirsan diskte en az 3-4 GB bos yer oldugundan
> emin ol.

## Calistirma sirasi

**1. Olay hattini dogrula** (XProtect erisimi varken)

```bash
python tools/test_event.py
```

Smart Client > Alarm Manager'da alarm gorunmeli. Gorunmuyorsa
`docs/analytics-event-protocol.md` icindeki sorun giderme tablosuna bak.

**2. XProtect'siz gelistirme**

```bash
python tools/mock_event_server.py        # terminal 1
python fire_watch.py --source test.mp4 --show   # terminal 2
```

`config.yaml` icinde `event_server: 127.0.0.1` olmali.

**3. Canli calistirma**

```bash
python fire_watch.py
```

## Parametreler

| Bayrak | Aciklama |
|---|---|
| `--source` | RTSP url veya video dosyasi (config'i ezer) |
| `--show` | Goruntuyu pencerede goster, guven skorlarini bas |
| `--dry-run` | Olay gonderme, sadece logla |

## Dokumanlar

- `docs/milestone-setup.md` - Management Client yapilandirmasi
- `docs/analytics-event-protocol.md` - XML formati, sorun giderme
- `docs/tuning.md` - esik degerlerini ayarlama
- `SPEC.md` - kapsam ve kabul kriterleri
