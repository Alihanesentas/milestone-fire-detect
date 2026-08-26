# Analytics Event protokolu

XProtect Event Server'a olay gondermenin en dogrudan yolu. HTTP formatinda XML,
varsayilan port 9090. MIP SDK veya Windows gerektirmez; saf socket ile Linux
uzerinden Python'dan gonderilebilir.

## Istek formati

```
POST / HTTP/1.1
Content-Type: text/xml
Content-Length: <govde uzunlugu>
Connection: Close

<?xml version="1.0" encoding="utf-8"?>
<AnalyticsEvent xmlns:i="http://www.w3.org/2001/XMLSchema-instance" xmlns="urn:milestone-systems">
  <EventHeader>
    <ID>{guid}</ID>
    <Timestamp>2026-08-26T14:03:11.412+03:00</Timestamp>
    <Type>Smoke Detected</Type>
    <Message>Duman tespiti - guven 0.87</Message>
    <Source>
      <Name>Kamera-01</Name>
    </Source>
  </EventHeader>
  <Description>6/8 kare pozitif</Description>
</AnalyticsEvent>
```

## Alanlar

| Alan | Kural |
|---|---|
| `ID` | Her olay icin yeni GUID. Ayni GUID tekrar gonderilirse yinelenen sayilabilir. |
| `Timestamp` | ISO 8601, saat dilimi offset'i dahil. Python: `datetime.now().astimezone().isoformat()` |
| `Type` | Management Client'ta tanimli analytics event adiyla **birebir** eslesmeli. |
| `Message` | Alarm listesinde operatorun gordugu metin. Kisa ve eyleme donuk olmali. |
| `Source > Name` | XProtect'teki kamera adi veya IP'si. Eslesmezse alarm kameraya baglanmaz. |
| `Description` | Serbest metin. Karar gerekcesini buraya yaz (kac kare, hangi ROI). |

## Sorun giderme

| Belirti | Muhtemel neden |
|---|---|
| Baglanti reddedildi | Analytics Events kapali, ya da Event Server yeniden baslatilmadi |
| Baglanti kuruldu ama alarm yok | `Type` degeri Management Client'taki tanimla eslesmiyor |
| Olay var, alarm yok | Alarm Definition olusturulmamis veya devre disi |
| Alarm var, kamera bagli degil | `Source > Name` XProtect'teki kamera adiyla eslesmiyor |
| Zaman asimi | Windows Firewall 9090'i engelliyor, ya da IP izinli listede degil |
| Bazi olaylar dusuyor | Ayni GUID tekrar gonderiliyor, ya da cok yuksek frekansta gonderim |

## Alternatif: Generic Event

Daha basit bir yol var: TCP/UDP uzerinden duz metin gonderip Management Client'ta
ifadeyle eslestirmek. Kurulumu daha kolay ama kaynak kamera baglama ve zengin alan
tasima yetenegi zayif. Bu projede analytics event tercih edildi.
