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

Bunlarin ornek karelerini kaydedip test setine eklemek, esik ayarini tahminden
cikarir.
