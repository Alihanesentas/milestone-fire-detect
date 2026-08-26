# Management Client yapilandirmasi

Admin yetkisi gerektirir. Yaklasik 10 dakika.

## 1. Analytics Events servisini ac

`Tools > Options > Analytics Events` sekmesi

- **Enabled** isaretle
- **Port**: 9090 (varsayilan)
- **Events allowed from**: analiz servisinin calisacagi makinenin IP'sini ekle.
  Test asamasinda "All network addresses" secilebilir, sonra daraltilmalidir.

> Bu ayar degistikten sonra **Event Server servisi yeniden baslatilmalidir**.
> Yeniden baslatilmazsa ayar aktif olmaz ve baglanti reddedilir.

## 2. Analytics event tanimlarini olustur

`Site Navigation > Rules and Events > Analytics Events` > sag tik > Add New

Uc tanim ekle, isimleri birebir asagidaki gibi olmali:

- `Smoke Detected`
- `Fire Detected`
- `Analytics Heartbeat`

Bu isimler `fire_watch.py` icinde gonderilen `<Type>` alanidir. Bir harf farki
olayin dusmesine neden olur.

## 3. Alarm tanimlarini olustur

`Site Navigation > Alarms > Alarm Definitions` > sag tik > Add New

`Smoke Detected` icin:
- **Triggering event**: Analytics Events > Smoke Detected
- **Sources**: ilgili kamera(lar)
- **Alarm manager**: oncelik ve atanacak kullanici grubu

Ayni islemi `Fire Detected` icin tekrarla. Ates alarminin onceligini daha yuksek ver.

## 4. Heartbeat kurali (opsiyonel ama onerilir)

`Rules and Events > Rules` altinda, `Analytics Heartbeat` olayi 120 saniyedir
gelmiyorsa uyari uretecek bir kural tanimla. Bu olmadan analiz servisi coktugunde
sistem sessizce korlesir ve kimse fark etmez.

## 5. Ayri kullanici hesabi

Analiz servisi icin XProtect'te ayri, sadece ilgili kamerayi okuma yetkisi olan
bir kullanici acilmali. Yonetici hesabiyla RTSP akisi cekilmemelidir.

## Dogrulama

```bash
python tools/test_event.py
python tools/test_event.py "Fire Detected"
```

Her ikisinde de Smart Client > Alarm Manager'da alarm satiri gorunmelidir.
