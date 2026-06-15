# Final Pipeline CARLA Canli Testi

## 0. Senaryo Fazlari

| Faz | Sure (tick) | CARLA | CIC | Beklenen safe mode | Amac |
|---|---:|---|---|---|---|
| baseline_normal | 24 | normal | Benign | normal_mode | Establish a clean baseline before the attack chain starts. |
| network_intrusion_probe | 24 | normal | mitm | monitoring_mode | Trigger the CIC branch while the vehicle dynamics remain nominal. |
| dos_sensor_corruption | 28 | dos | dos | degraded_safe_mode | Mix network pressure with packet loss/stale sensor observations in the V6 branch. |
| hallucinated_sudden_brake | 24 | sudden_brake | Benign | monitoring_mode | Force a hard brake while the front camera context stays clear to expose a visual hallucination risk. |
| coordinated_control_takeover | 30 | lane_deviation | scanning | emergency_safe_mode | Escalate into a coordinated multi-layer anomaly with steering deviation plus a live CIC alert. |

## Test Metrikleri

| Metrik | Risk | Safe mode |
|---|---:|---:|
| Accuracy | 0.692 | 0.308 |
| Macro F1 | 0.567 | 0.263 |
## Gorsel Karsilastirma

| # | Faz | Gorsel p | Kamera on gorunen aktor | Sensor front distance | Fren | Aciklama | Image |
|---|---|---:|---:|---:|---:|---|---|
| 16 | hallucinated_sudden_brake | 0.820 | 0 | 64.8 | 1.00 | Ani fren icin gorselde yakin tehlike yok; anomalilik olasiligi yuksek. | images/133623_hallucinated_sudden_brake.png |
| 17 | hallucinated_sudden_brake | 0.820 | 0 | 62.6 | 1.00 | Ani fren icin gorselde yakin tehlike yok; anomalilik olasiligi yuksek. | images/133628_hallucinated_sudden_brake.png |
| 18 | hallucinated_sudden_brake | 0.820 | 0 | 61.5 | 1.00 | Ani fren icin gorselde yakin tehlike yok; anomalilik olasiligi yuksek. | images/133633_hallucinated_sudden_brake.png |
| 19 | hallucinated_sudden_brake | 0.820 | 0 | 60.8 | 1.00 | Ani fren icin gorselde yakin tehlike yok; anomalilik olasiligi yuksek. | images/133638_hallucinated_sudden_brake.png |
| 20 | coordinated_control_takeover | 0.600 | 0 | 60.2 | 0.00 | Konum/yon saldirisi gorsel yogunluk ve cevre nesneleriyle karsilastirildi. | images/133643_coordinated_control_takeover.png |
| 21 | coordinated_control_takeover | 0.600 | 0 | 59.7 | 0.00 | Konum/yon saldirisi gorsel yogunluk ve cevre nesneleriyle karsilastirildi. | images/133648_coordinated_control_takeover.png |
| 22 | coordinated_control_takeover | 0.600 | 0 | 59.2 | 0.00 | Konum/yon saldirisi gorsel yogunluk ve cevre nesneleriyle karsilastirildi. | images/133653_coordinated_control_takeover.png |
| 23 | coordinated_control_takeover | 0.600 | 0 | 58.8 | 0.00 | Konum/yon saldirisi gorsel yogunluk ve cevre nesneleriyle karsilastirildi. | images/133658_coordinated_control_takeover.png |
| 24 | coordinated_control_takeover | 0.600 | 0 | 58.3 | 0.00 | Konum/yon saldirisi gorsel yogunluk ve cevre nesneleriyle karsilastirildi. | images/133663_coordinated_control_takeover.png |
| 25 | coordinated_control_takeover | 0.600 | 0 | 57.9 | 0.00 | Konum/yon saldirisi gorsel yogunluk ve cevre nesneleriyle karsilastirildi. | images/133668_coordinated_control_takeover.png |

# Otonom Arac Guvenlik Izleme Raporu

## 1. Yonetici Ozeti

Bu rapor 26 olaylik izleme penceresi icin uretilmistir. Sistem 19 olayda saldiri/anomali, 7 olayda normal durum karari vermistir. Nihai guvenli mod onerisi: **Acil Guvenli Mod**.

| Metrik | Deger |
|---|---:|
| Toplam olay | 26 |
| Attack/anomali karari | 19 (73.1%) |
| Normal karar | 7 (26.9%) |
| Insan incelemesi gereken olay | 19 (73.1%) |
| Guvenli mod gerektiren olay | 24 (92.3%) |
| Onerilen guvenli mod | Acil Guvenli Mod |

## 2. Nihai Karar

Sistem **Acil Guvenli Mod** onermektedir. Bu karar, izleme penceresinde 19 kritik, 5 yuksek ve 0 orta seviye bulgu olusmasi nedeniyle verilmistir. Aracin operasyonel riski yuksek kabul edilmeli, hiz/rota kontrolu kisitlanmali ve guvenli durus veya kontrollu devralma senaryosu uygulanmalidir.

## 3. Katman Bazli Bulgular

| Katman | Tetiklenen olay | Seviye dagilimi | Yorum |
|---|---:|---|---|
| CIC ag katmani | 17 | critical: 15, low: 9, medium: 2 | Ag katmani bulgulari izlenmistir. |
| CARLA davranis/sensor katmani | 19 | high: 16, low: 7, medium: 3 | Davranis/sensor anomalileri karar uzerinde belirleyici oldu. |
| nuScenes gorsel tutarlilik katmani | 10 | high: 4, low: 10, medium: 12 | Gorsel tutarlilik sinyali izlenmistir. |
| Fusion karar katmani | 19 | critical: 11, high: 8, low: 7 | Katman sinyallerini birlestirerek nihai risk kararini destekledi. |

## 4. Tehdit Sikliklari

| Tehdit/anomali turu | Olay sayisi | Oran |
|---|---:|---:|
| lane_deviation | 9 | 34.6% |
| dos | 5 | 19.2% |
| sudden_brake | 4 | 15.4% |
| position_spoofing | 1 | 3.8% |

## 5. Guvenli Mod Dagilimi

| Sinif | Olay sayisi | Oran |
|---|---:|---:|
| Kisitli Guvenli Mod | 5 | 19.2% |
| Acil Guvenli Mod | 19 | 73.1% |
| Normal Mod | 2 | 7.7% |

## 6. Oncelikli Olay Ornekleri

| # | Zaman | Risk | Saldiri turu | Safe mode | CARLA p | CIC p | Gorsel p |
|---:|---:|---|---|---|---:|---:|---:|
| 1 | 985.5045231245458 | attack | lane_deviation | Acil Guvenli Mod | 0.513 | 0.000 | 0.120 |
| 3 | 986.0045231319964 | attack | lane_deviation | Acil Guvenli Mod | 0.756 | 0.000 | 0.120 |
| 4 | 986.2545231357217 | attack | lane_deviation | Acil Guvenli Mod | 0.855 | 0.000 | 0.120 |
| 5 | 986.504523139447 | attack | lane_deviation | Acil Guvenli Mod | 0.847 | 0.796 | 0.120 |
| 6 | 986.7545231431723 | attack | lane_deviation | Acil Guvenli Mod | 0.876 | 0.958 | 0.120 |
| 7 | 987.0045231468976 | attack | lane_deviation | Acil Guvenli Mod | 0.851 | 0.786 | 0.120 |
| 8 | 987.2545231506228 | attack | lane_deviation | Acil Guvenli Mod | 0.879 | 0.944 | 0.120 |
| 9 | 987.5045231543481 | attack | lane_deviation | Acil Guvenli Mod | 0.865 | 0.920 | 0.120 |
| 10 | 987.7545231580734 | attack | position_spoofing | Acil Guvenli Mod | 0.879 | 1.000 | 0.500 |
| 11 | 988.0045231617987 | attack | dos | Kisitli Guvenli Mod | 0.898 | 1.000 | 0.500 |
| 12 | 988.254523165524 | attack | dos | Kisitli Guvenli Mod | 0.899 | 1.000 | 0.500 |
| 13 | 988.5045231692493 | attack | dos | Kisitli Guvenli Mod | 0.896 | 1.000 | 0.500 |

## 7. Nihai Yorum ve Oneriler

- Izleme penceresinde 26 olay incelenmis, 19 olay saldiri/anomali olarak degerlendirilmistir.
- En baskin tehditler: lane_deviation (9), dos (5), sudden_brake (4), position_spoofing (1).
- Nihai karar **Acil Guvenli Mod** olarak atanmistir; bu karar CARLA davranis/sensor katmani ve fusion karar katmanindaki kritik bulgularla desteklenmektedir.
- Onerilen operasyonel aksiyon: araci kontrollu sekilde kisitli/guvenli davranisa almak, riskli manevralari engellemek, telemetriyi kaydetmek ve insan operator incelemesine aktarmak.
- CIC ve gorsel katman bu pencerede esik ustu bulgu uretmedigi icin ana risk kaynagi davranis/sensor anomalileri olarak yorumlanmalidir.

## 8. Ollama Durumu

Ollama yorumu istenmedi.

## 9. Notlar

- Bu rapor karar destek amaclidir; nihai operasyon karari sistem politikasi ve insan denetimiyle birlikte verilmelidir.
- Safe mode karari CIC, CARLA, nuScenes gorsel tutarlilik ve fusion karar katmaninin birlikte degerlendirilmesiyle uretilmistir.
- Kritik siniflarda temkinli karar verilmesi, otonom arac guvenligi acisindan tercih edilen davranistir.
