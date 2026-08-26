# CLAUDE.md

Bu dosya Claude Code icin proje baglamidir. Yeni bir oturum acildiginda once bunu oku.

## Proje nedir

Milestone XProtect VMS uzerindeki kameralardan RTSP ile video alip duman/ates
tespiti yapan ve sonucu XProtect'e analytics event olarak geri gonderen tek
proseslik bir Python servisi. Alarm XProtect'in kendi Alarm Manager'inda dogar,
ayri bir arayuz yoktur.

Akis: `XProtect -> RTSP -> kare alma -> tespit -> zamansal dogrulama -> analytics event -> XProtect alarm`

## Kisitlar - bunlara uy

- **Tek proses, tek dosya.** Ana uygulama `fire_watch.py` icinde kalir. Mikroservise
  bolme, mesaj kuyrugu ekleme, async framework getirme. Bu bilincli bir karardir.
- **Model egitilmez.** Hazir egitilmis YOLOv8 agirliklari kullanilir. Egitim
  pipeline'i, veri seti indirme scripti, augmentation kodu yazma.
- **Metadata / bounding box overlay yok.** Ciktimiz binary: var / yok. XProtect'e
  sadece analytics event gider.
- **Bagimlilik ekleme.** requirements.txt'teki uc paketle yetin. Yeni bir paket
  gerektigini dusunuyorsan once sor.
- **Zamansal dogrulama kaldirilamaz.** Tek karelik pozitifi olaya cevirmek yasak.
  Confirmer sinifi bu projenin en kritik parcasi.
- **Olay gonderimi hata verirse uygulama durmaz.** Sadece loglanir, dongu devam eder.

## Dosya haritasi

| Dosya | Ne yapar |
|---|---|
| `fire_watch.py` | Ana servis. EventSender, Detector, Confirmer, FrameSource siniflari. |
| `config.yaml` | Tum ayarlar. Kod icine sabit deger yazma, buraya ekle. |
| `tools/test_event.py` | XProtect'e tek sahte olay gonderir. Boru hatti dogrulamasi. |
| `tools/mock_event_server.py` | Yerelde 9090'i dinler, gelen XML'i basar. XProtect'siz gelistirme. |
| `docs/milestone-setup.md` | Management Client tarafinda yapilacaklar. |
| `docs/analytics-event-protocol.md` | XML formati ve sorun giderme tablosu. |
| `docs/tuning.md` | Esik degerlerini ayarlama. |

## Gelistirme sirasi

XProtect erisimi her zaman yok. Bu yuzden:

1. `python tools/mock_event_server.py` calistir (ayri terminal)
2. `config.yaml` icinde `event_server: 127.0.0.1` yap
3. `python fire_watch.py --source test.mp4 --show` ile gelistir
4. Sadece son adimda gercek XProtect IP'sine gec

## Sik yapilan hatalar

- `source_name` degeri XProtect'teki kamera adiyla **birebir** eslesmezse olay
  dusmez ama alarm kameraya baglanmaz. Buyuk/kucuk harf ve bosluk onemli.
- Management Client'ta Analytics Events ayari degistirilince **Event Server
  yeniden baslatilmali**, yoksa ayar aktif olmaz.
- Model dosyasindaki sinif isimleri (`fire`, `Fire`, `flame`...) degisken. Model
  yuklenirken loglanan isimleri `config.yaml`'daki `fire_labels`/`smoke_labels`
  ile karsilastir.
- RTSP'de buffer birikimi gecikme yaratir. `FrameSource` bunu `grab()` ile
  cozuyor, o mantigi bozma.

## Kod stili

Turkce log mesajlari (ASCII, Turkce karakter yok - Windows konsolu bozuyor).
Yorumlar Turkce. Degisken ve sinif isimleri Ingilizce. Type hint zorunlu degil.
