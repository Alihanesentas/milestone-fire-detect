---
name: milestone-analytics-event
description: Milestone XProtect Event Server'a analytics event gonderen veya bu olaylarin formatini/hata ayiklamasini iceren her is icin kullan. Tetikleyiciler - analytics event, XProtect alarm, Event Server, port 9090, AnalyticsEvent XML, Smart Client alarm gorunmuyor, Milestone olay gondermek, generic event, MIP SDK protokol entegrasyonu.
---

# Milestone analytics event gonderimi

## Ne zaman

XProtect'e olay/alarm gonderilecegi zaman. Bu projede tek geri bildirim
mekanizmasi budur - metadata stream, MIP SDK plugin veya REST API kullanilmaz.

## Protokol

Event Server'a TCP baglantisi acilir, HTTP formatinda XML govde gonderilir.
Varsayilan port 9090. Yanit beklemek zorunlu degildir.

```
POST / HTTP/1.1
Content-Type: text/xml
Content-Length: <govde byte uzunlugu>
Connection: Close

<govde>
```

Govde `urn:milestone-systems` namespace'inde `AnalyticsEvent` kok elemani olmali:

```xml
<?xml version="1.0" encoding="utf-8"?>
<AnalyticsEvent xmlns:i="http://www.w3.org/2001/XMLSchema-instance" xmlns="urn:milestone-systems">
  <EventHeader>
    <ID>{yeni guid}</ID>
    <Timestamp>{ISO 8601, offset dahil}</Timestamp>
    <Type>{Management Client'ta tanimli olay adi}</Type>
    <Message>{operatorun gordugu metin}</Message>
    <Source><Name>{kamera adi veya IP}</Name></Source>
  </EventHeader>
  <Description>{karar gerekcesi}</Description>
</AnalyticsEvent>
```

## Zorunlu kurallar

1. **`Content-Length` byte cinsinden hesaplanmali**, karakter degil. Turkce karakter
   iceren mesajlarda `len(str)` yanlis sonuc verir; `len(body.encode("utf-8"))` kullan.
2. **`Type` degeri Management Client'taki tanimla birebir eslesmeli.** Bu projede
   gecerli degerler: `Smoke Detected`, `Fire Detected`, `Analytics Heartbeat`.
   Yeni bir tip ekleniyorsa Management Client tarafinda da tanimlanmasi gerektigi
   kullaniciya soylenmeli.
3. **Her olay yeni GUID almali.** `uuid.uuid4()`.
4. **`Timestamp` saat dilimi offset'i icermeli.** `datetime.now().astimezone().isoformat()`.
   Naive datetime gonderilirse olay yanlis zamana dusler.
5. **`Source > Name` config'ten gelmeli**, koda sabit yazilmamali.
6. **Gonderim hatasi uygulamayi durdurmamali.** `OSError` yakalanir, loglanir,
   dongu devam eder. Yangin tespiti servisinin agdaki gecici bir sorun yuzunden
   olmesi kabul edilemez.
7. **Yeniden deneme dongusu kurma.** Kacirilan bir olay icin sonsuz retry yerine
   tek deneme + log tercih edilir; bir sonraki pozitif kare zaten yeni olay uretir.

## Referans implementasyon

`fire_watch.py` icindeki `EventSender` sinifi ve `tools/test_event.py`. Yeni bir
olay gonderimi gerekiyorsa bu siniftan gec, paralel bir gonderim kodu yazma.

## Test

XProtect erisimi olmadan `tools/mock_event_server.py` calistirilir, config'te
`event_server: 127.0.0.1` yapilir. Gelen XML terminale basilir.

XProtect erisimi varken `tools/test_event.py` calistirilir ve Smart Client >
Alarm Manager kontrol edilir.

## Sorun giderme

| Belirti | Neden |
|---|---|
| Connection refused | Analytics Events kapali veya Event Server yeniden baslatilmadi |
| Baglanti var, alarm yok | `Type` eslesmiyor, ya da Alarm Definition yok |
| Alarm var, kamera bagli degil | `Source > Name` XProtect'teki kamera adiyla eslesmiyor |
| Timeout | Firewall 9090'i engelliyor veya IP izinli listede degil |

Bu tabloyu genisletirken `docs/analytics-event-protocol.md` ile senkron tut.
