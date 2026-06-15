# Otonom Arac Guvenlik Izleme Raporu

## 1. Yonetici Ozeti

Bu rapor 200 olaylik izleme penceresi icin uretilmistir. Sistem 136 olayda saldiri/anomali, 64 olayda normal durum karari vermistir. Nihai guvenli mod onerisi: **Acil Guvenli Mod**.

| Metrik | Deger |
|---|---:|
| Toplam olay | 200 |
| Attack/anomali karari | 136 (68.0%) |
| Normal karar | 64 (32.0%) |
| Insan incelemesi gereken olay | 136 (68.0%) |
| Guvenli mod gerektiren olay | 136 (68.0%) |
| Onerilen guvenli mod | Acil Guvenli Mod |

## 2. Nihai Karar

Sistem **Acil Guvenli Mod** onermektedir. Bu karar, izleme penceresinde 136 kritik, 0 yuksek ve 0 orta seviye bulgu olusmasi nedeniyle verilmistir. Aracin operasyonel riski yuksek kabul edilmeli, hiz/rota kontrolu kisitlanmali ve guvenli durus veya kontrollu devralma senaryosu uygulanmalidir.

## 3. Katman Bazli Bulgular

| Katman | Tetiklenen olay | Seviye dagilimi | Yorum |
|---|---:|---|---|
| CIC ag katmani | 0 | low: 200 | Bu pencerede esik ustu bulgu uretmedi. |
| CARLA davranis/sensor katmani | 136 | critical: 92, high: 26, low: 64, medium: 18 | Davranis/sensor anomalileri karar uzerinde belirleyici oldu. |
| nuScenes gorsel tutarlilik katmani | 0 | low: 200 | Bu pencerede esik ustu bulgu uretmedi. |
| Fusion karar katmani | 136 | critical: 136, low: 64 | Katman sinyallerini birlestirerek nihai risk kararini destekledi. |

## 4. Tehdit Sikliklari

| Tehdit/anomali turu | Olay sayisi | Oran |
|---|---:|---:|
| heading_spoofing | 22 | 11.0% |
| sensor_noise | 20 | 10.0% |
| gps_spoofing | 20 | 10.0% |
| dos | 17 | 8.5% |
| speed_spoofing | 17 | 8.5% |
| position_spoofing | 15 | 7.5% |
| lane_deviation | 13 | 6.5% |
| sudden_brake | 11 | 5.5% |
| delayed_sensor_attack | 1 | 0.5% |

## 5. Guvenli Mod Dagilimi

| Sinif | Olay sayisi | Oran |
|---|---:|---:|
| Acil Guvenli Mod | 136 | 68.0% |
| Normal Mod | 64 | 32.0% |

## 6. Oncelikli Olay Ornekleri

| # | Zaman | Risk | Saldiri turu | Safe mode | CARLA p | CIC p | Gorsel p |
|---:|---:|---|---|---|---:|---:|---:|
| 0 | 1779212898.3934238 | attack | lane_deviation | Acil Guvenli Mod | 0.627 | 0.000 | 0.180 |
| 2 | 1779212962.2976928 | attack | dos | Kisitli Guvenli Mod | 0.771 | 0.000 | 0.500 |
| 3 | 1779212934.4065194 | attack | sensor_noise | Izleme Modu | 0.993 | 0.002 | 0.500 |
| 4 | 1779212816.6771135 | attack | position_spoofing | Acil Guvenli Mod | 0.968 | 0.002 | 0.420 |
| 6 | 1779213045.1833088 | attack | heading_spoofing | Kisitli Guvenli Mod | 0.858 | 0.000 | 0.180 |
| 7 | 1779212823.5263176 | attack | speed_spoofing | Kisitli Guvenli Mod | 0.935 | 0.000 | 0.500 |
| 8 | 1779212840.8920867 | attack | speed_spoofing | Kisitli Guvenli Mod | 0.975 | 0.000 | 0.500 |
| 9 | 1779212776.5570138 | attack | gps_spoofing | Kisitli Guvenli Mod | 0.924 | 0.000 | 0.420 |
| 10 | 1779213045.6523046 | attack | heading_spoofing | Kisitli Guvenli Mod | 0.947 | 0.000 | 0.420 |
| 14 | 1779212881.833623 | attack | sudden_brake | Acil Guvenli Mod | 0.946 | 0.000 | 0.180 |
| 15 | 1779212822.8202488 | attack | speed_spoofing | Kisitli Guvenli Mod | 0.969 | 0.000 | 0.500 |
| 16 | 1779212777.1653347 | attack | gps_spoofing | Kisitli Guvenli Mod | 0.977 | 0.000 | 0.420 |

## 7. Nihai Yorum ve Oneriler

- Izleme penceresinde 200 olay incelenmis, 136 olay saldiri/anomali olarak degerlendirilmistir.
- En baskin tehditler: heading_spoofing (22), sensor_noise (20), gps_spoofing (20), dos (17), speed_spoofing (17).
- Nihai karar **Acil Guvenli Mod** olarak atanmistir; bu karar CARLA davranis/sensor katmani ve fusion karar katmanindaki kritik bulgularla desteklenmektedir.
- Onerilen operasyonel aksiyon: araci kontrollu sekilde kisitli/guvenli davranisa almak, riskli manevralari engellemek, telemetriyi kaydetmek ve insan operator incelemesine aktarmak.
- CIC ve gorsel katman bu pencerede esik ustu bulgu uretmedigi icin ana risk kaynagi davranis/sensor anomalileri olarak yorumlanmalidir.

## 8. Ollama Durumu

Ollama servisi calisti (`model=mistral:latest`). Ham LLM metni JSON raporda saklanmistir; kullaniciya sunulan nihai yorum bu raporda sade ve yapilandirilmis bicimde verilmistir.

## 9. Notlar

- Bu rapor karar destek amaclidir; nihai operasyon karari sistem politikasi ve insan denetimiyle birlikte verilmelidir.
- Safe mode karari CIC, CARLA, nuScenes gorsel tutarlilik ve fusion karar katmaninin birlikte degerlendirilmesiyle uretilmistir.
- Kritik siniflarda temkinli karar verilmesi, otonom arac guvenligi acisindan tercih edilen davranistir.
