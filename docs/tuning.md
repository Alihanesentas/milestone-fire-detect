# Esik ayari

Bu projede modelin dogrulugundan cok, **yanlis alarm orani** belirleyicidir.
Operatorun guvenini kaybettiren sey kacirilan yangin degil, gunde on kere calan
bos alarmdir.

## Parametreler

| Parametre | Etkisi | Baslangic |
|---|---|---|
| `conf_threshold` | Kare basina pozitif sayilma esigi. Yukseltince yanlis alarm azalir, kacirma artar. | 0.45 |
| `window` | Kayan pencere boyutu (kare). `target_fps` ile birlikte sureyi belirler. | 8 |
| `min_hits` | Penceredeki min pozitif kare. Yukseltince israr sarti artar. | 5 |
| `cooldown_sec` | Alarm sonrasi sessizlik. Ayni olay icin tekrar alarm uretmeyi engeller. | 300 |
| `target_fps` | Islenen kare/saniye. Yukseltmek CPU maliyeti disinda dogruluk kazandirmaz. | 4 |

`window: 8` ve `target_fps: 4` ile pencere yaklasik 2 saniyeyi kapsar. `min_hits: 5`
yani "2 saniyede en az 1.25 saniye pozitif" demektir.

## Ayar yontemi

1. `--dry-run --show` ile bos koridor / normal ortam goruntusu uzerinde en az
   2 saat calistir. Loglara bakip kac kere ADAY durumuna girildigini say.
2. ADAY'a sik giriliyorsa once `conf_threshold`'u 0.05 arttir.
3. Hala ADAY'a giriyorsa `min_hits`'i arttir. `window`'u buyutmek alarm gecikmesini
   arttirir, once `min_hits` denenmelidir.
4. Sonra test videosuyla kacirma tarafini kontrol et. Alarm 5 saniyeden gec
   geliyorsa `min_hits`'i geri dusur.

Bu ayarlar tahminle degil, **o kameranin kendi goruntusuyle** yapilmalidir. Farkli
aci ve isik kosullarinda farkli degerler cikar.

## Bilinen yanlis alarm kaynaklari

- Gun batimi / gun dogumu, pencereden vuran turuncu isik
- Arac farlari, acil durum lambasi, kirmizi/turuncu kiyafet
- Kalorifer buhari, sigara dumani, temizlik buhari
- Kamera lensinde yansima veya kir
- Otomatik pozlama sonrasi ani parlaklik degisimi
- **Yazici/elektronik cihaz isisi-parliltisi** - asagidaki teste bakin

Bunlarin ornek karelerini kaydedip test setine eklemek, esik ayarini tahminden
cikarir.

## Gercek veriyle yapilan test (Kaggle unidpro/fire-and-smoke-dataset)

`fire_smoke.pt` (luminous0219/fire-and-smoke-detection-yolov8) varsayilan
ayarlarla (`conf_threshold=0.45`, `window=8`, `min_hits=5`, `target_fps=4`)
3 gercek etiketli video uzerinde test edildi:

| Video | Gercek olay | Sistem alarmi | Gecikme | SPEC (<=5sn) |
|---|---|---|---|---|
| `printer31` | duman, 27sn | **1.2sn (sahte alarm)** | - | Basarisiz - gercek olaydan once sahte alarm |
| `bucket11` | ates, 9sn (kucuk alev) | 38.4sn | 29.4sn | Basarisiz - gec kaliyor |
| `roomfire41` | duman, 776sn | 780sn | 4sn | Basarili |
| `roomfire41` | ates, 787sn | 794.4sn | 7.4sn | Sinirda basarisiz |

**Cikarilan dersler:**

1. **Yazici isisi/parliltisi surekli bir yanlis "duman" sinyali uretiyor**
   (guven ~0.45-0.65 araliginda, video basindan itibaren surekli). Zamansal
   dogrulama (window+min_hits) bunu FILTRELEMIYOR, cunku sinyal izole degil,
   surekli - `Confirmer` sadece tek karelik/aralikli yanlis pozitifleri
   eler (bkz. `roomfire41`'deki izole yanlis pozitifler basariyla elendi).
   Kamera acisinda yazici/elektronik cihaz gibi surekli isi kaynagi varsa
   ya ROI ile kadraj disi birakilmali ya da o kamera icin esik ayrica
   yukseltilmeli.
2. **Kucuk/uzak alev gec tespit ediliyor** (`bucket11`: etiketlerde alev
   bolgesi birkac piksel genisliginde). Bu, SPEC.md risk tablosundaki
   "kamera acisinda duman kucuk goruntuleniyor" riskinin dogrulanmis hali -
   cozum tahminle esik oynamak degil, kamera konumlandirma/ROI.
3. Bu iki bulgu birbiriyle geriliyor: `conf_threshold`'u yazici yanlis
   alarmini bastiracak kadar yukseltmek (>0.65), `bucket11`'deki zaten zayif
   (0.64 guvenli) gercek tespiti de bastirir. Tek bir global esik degeri
   ile ikisini ayni anda cozmek bu model icin mumkun degil - kamera bazinda
   ROI/konum ayari sart.
