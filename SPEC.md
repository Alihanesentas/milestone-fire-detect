# Proje spesifikasyonu

## Amac

Mevcut Milestone XProtect kamera altyapisi uzerinde, duman veya ates goruldugunde
operatore XProtect'in kendi alarm arayuzunden uyari veren bir gorsel erken uyari
katmani kurmak.

## Kapsam icinde

- Tek kameradan RTSP ile canli goruntu alma, kopan baglantiyi toparlama
- Kare basina duman/ates siniflandirmasi (hazir egitilmis model)
- Yanlis alarmi engelleyen zamansal dogrulama (kayan pencere + cooldown)
- XProtect Event Server'a analytics event gonderme (`Smoke Detected`, `Fire Detected`)
- Servis sagligi icin periyodik heartbeat olayi
- Demo modu: video dosyasi uzerinden calisma, olay gondermeden test

## Kapsam disinda

- Model egitimi veya fine-tune
- Bounding box / metadata overlay
- Coklu kamera, yatay olcekleme
- Ayri web arayuzu, veritabani, raporlama
- SMS/e-posta bildirimi (XProtect kural motoruna birakildi)

## Kabul kriterleri

1. `tools/test_event.py` calistirildiginda Smart Client Alarm Manager'da alarm
   satiri gorunur ve ilgili kameraya baglidir.
2. Test videosunda duman/ates iceren bolumde en fazla 5 saniye icinde alarm uretir.
3. Bos koridor goruntusunde 2 saat kesintisiz calismada 0 yanlis alarm uretir.
4. RTSP baglantisi kesilip geri geldiginde servis manuel mudahale olmadan devam eder.
5. Servis durdurulursa heartbeat kesilir; XProtect tarafinda bu kurala baglanabilir.

## Yol haritasi

**Asama 1 - olay hatti (oncelik: en yuksek)**
XProtect'e olay gonderimi calistigi dogrulanir. Detection'a hic dokunulmaz.
Bu asama gecmeden digerlerine baslanmaz.

**Asama 2 - video hatti**
RTSP acilir, kare alinir, yeniden baglanma test edilir.

**Asama 3 - tespit**
Hazir model takilir, guven skorlari test videosunda gozlemlenir.

**Asama 4 - dogrulama ve ayar**
Zamansal dogrulama devreye alinir, esikler canli goruntude ayarlanir.

## Riskler

| Risk | Etki | Onlem |
|---|---|---|
| XProtect admin erisimi bizde degil | Test dongusu yavaslar | `mock_event_server.py` ile yerelde gelistir |
| Port 9090 kapali / IP izinli degil | Olay hic gitmez | Asama 1'i once bitir |
| Hazir modelin sinif isimleri farkli | Hic tetiklenmez | Model yuklenirken sinif isimleri loglanir |
| Gun batimi, far, buhar kaynakli yanlis alarm | Guven kaybi | Kayan pencere + cooldown + canli esik ayari |
| Kamera acisinda duman kucuk goruntuleniyor | Kacirma | ROI kirpma veya kamera secimi degisikligi |

## Onemli not

Bu sistem EN 54 gibi yangin algilama standartlarina gore sertifikali bir cihaz
degildir ve mevcut yangin algilama altyapisinin yerine gecemez. Onun yaninda,
tamamlayici bir gorsel erken uyari katmani olarak konumlandirilmalidir. Teslim
sirasinda bu ayrim yazili olarak belirtilmelidir.
