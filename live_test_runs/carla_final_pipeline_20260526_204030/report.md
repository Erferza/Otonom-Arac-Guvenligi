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
| Accuracy | 0.692 | 0.346 |
| Macro F1 | 0.609 | 0.307 |
## Gorsel Karsilastirma

| # | Faz | Gorsel p | Kamera on gorunen aktor | Sensor front distance | Fren | Aciklama | Image |
|---|---|---:|---:|---:|---:|---|---|
| 16 | hallucinated_sudden_brake | 0.820 | 0 | 9999.0 | 1.00 | Ani fren icin gorselde yakin tehlike yok; anomalilik olasiligi yuksek. | images/077913_hallucinated_sudden_brake.png |
| 17 | hallucinated_sudden_brake | 0.820 | 0 | 9999.0 | 1.00 | Ani fren icin gorselde yakin tehlike yok; anomalilik olasiligi yuksek. | images/077918_hallucinated_sudden_brake.png |
| 18 | hallucinated_sudden_brake | 0.820 | 0 | 9999.0 | 1.00 | Ani fren icin gorselde yakin tehlike yok; anomalilik olasiligi yuksek. | images/077923_hallucinated_sudden_brake.png |
| 19 | hallucinated_sudden_brake | 0.820 | 0 | 9999.0 | 1.00 | Ani fren icin gorselde yakin tehlike yok; anomalilik olasiligi yuksek. | images/077928_hallucinated_sudden_brake.png |
| 20 | coordinated_control_takeover | 0.600 | 0 | 9999.0 | 0.00 | Konum/yon saldirisi gorsel yogunluk ve cevre nesneleriyle karsilastirildi. | images/077933_coordinated_control_takeover.png |
| 21 | coordinated_control_takeover | 0.600 | 0 | 9999.0 | 0.00 | Konum/yon saldirisi gorsel yogunluk ve cevre nesneleriyle karsilastirildi. | images/077938_coordinated_control_takeover.png |
| 22 | coordinated_control_takeover | 0.600 | 0 | 9999.0 | 0.00 | Konum/yon saldirisi gorsel yogunluk ve cevre nesneleriyle karsilastirildi. | images/077943_coordinated_control_takeover.png |
| 23 | coordinated_control_takeover | 0.600 | 0 | 9999.0 | 0.00 | Konum/yon saldirisi gorsel yogunluk ve cevre nesneleriyle karsilastirildi. | images/077948_coordinated_control_takeover.png |
| 24 | coordinated_control_takeover | 0.600 | 0 | 9999.0 | 0.00 | Konum/yon saldirisi gorsel yogunluk ve cevre nesneleriyle karsilastirildi. | images/077953_coordinated_control_takeover.png |
| 25 | coordinated_control_takeover | 0.600 | 0 | 9999.0 | 0.00 | Konum/yon saldirisi gorsel yogunluk ve cevre nesneleriyle karsilastirildi. | images/077958_coordinated_control_takeover.png |

# Otonom Arac Guvenlik Izleme Raporu

## 1. Yonetici Ozeti

Bu rapor 26 olaylik izleme penceresi icin uretilmistir. Sistem 17 olayda saldiri/anomali, 9 olayda normal durum karari vermistir. Nihai guvenli mod onerisi: **Acil Guvenli Mod**.

| Metrik | Deger |
|---|---:|
| Toplam olay | 26 |
| Attack/anomali karari | 17 (65.4%) |
| Normal karar | 9 (34.6%) |
| Insan incelemesi gereken olay | 17 (65.4%) |
| Guvenli mod gerektiren olay | 23 (88.5%) |
| Onerilen guvenli mod | Acil Guvenli Mod |

## 2. Nihai Karar

Sistem **Acil Guvenli Mod** onermektedir. Bu karar, izleme penceresinde 19 kritik, 4 yuksek ve 0 orta seviye bulgu olusmasi nedeniyle verilmistir. Aracin operasyonel riski yuksek kabul edilmeli, hiz/rota kontrolu kisitlanmali ve guvenli durus veya kontrollu devralma senaryosu uygulanmalidir.

## 3. Katman Bazli Bulgular

| Katman | Tetiklenen olay | Seviye dagilimi | Yorum |
|---|---:|---|---|
| CIC ag katmani | 17 | critical: 15, low: 9, medium: 2 | Ag katmani bulgulari izlenmistir. |
| CARLA davranis/sensor katmani | 17 | high: 13, low: 9, medium: 4 | Davranis/sensor anomalileri karar uzerinde belirleyici oldu. |
| nuScenes gorsel tutarlilik katmani | 10 | high: 4, low: 10, medium: 12 | Gorsel tutarlilik sinyali izlenmistir. |
| Fusion karar katmani | 17 | critical: 10, high: 7, low: 9 | Katman sinyallerini birlestirerek nihai risk kararini destekledi. |

## 4. Tehdit Sikliklari

| Tehdit/anomali turu | Olay sayisi | Oran |
|---|---:|---:|
| lane_deviation | 7 | 26.9% |
| sudden_brake | 4 | 15.4% |
| dos | 3 | 11.5% |
| sensor_noise | 2 | 7.7% |
| gps_spoofing | 1 | 3.8% |

## 5. Guvenli Mod Dagilimi

| Sinif | Olay sayisi | Oran |
|---|---:|---:|
| Kisitli Guvenli Mod | 4 | 15.4% |
| Acil Guvenli Mod | 19 | 73.1% |
| Normal Mod | 3 | 11.5% |

## 6. Oncelikli Olay Ornekleri

| # | Zaman | Risk | Saldiri turu | Safe mode | CARLA p | CIC p | Gorsel p |
|---:|---:|---|---|---|---:|---:|---:|
| 3 | 583.0899674519897 | attack | lane_deviation | Acil Guvenli Mod | 0.744 | 0.000 | 0.120 |
| 4 | 583.3399674557149 | attack | lane_deviation | Acil Guvenli Mod | 0.794 | 0.000 | 0.120 |
| 5 | 583.5899674594402 | attack | lane_deviation | Acil Guvenli Mod | 0.822 | 0.796 | 0.120 |
| 6 | 583.8399674631655 | attack | lane_deviation | Acil Guvenli Mod | 0.825 | 0.958 | 0.120 |
| 7 | 584.0899674668908 | attack | lane_deviation | Acil Guvenli Mod | 0.802 | 0.786 | 0.120 |
| 8 | 584.3399674706161 | attack | lane_deviation | Acil Guvenli Mod | 0.822 | 0.944 | 0.120 |
| 9 | 584.5899674743414 | attack | lane_deviation | Acil Guvenli Mod | 0.822 | 0.920 | 0.120 |
| 10 | 584.8399674780667 | attack | gps_spoofing | Kisitli Guvenli Mod | 0.824 | 1.000 | 0.500 |
| 11 | 585.089967481792 | attack | sensor_noise | Kisitli Guvenli Mod | 0.837 | 1.000 | 0.500 |
| 12 | 585.3399674855173 | attack | dos | Kisitli Guvenli Mod | 0.866 | 1.000 | 0.500 |
| 13 | 585.5899674892426 | attack | dos | Kisitli Guvenli Mod | 0.854 | 1.000 | 0.500 |
| 14 | 585.8399674929678 | attack | dos | Kisitli Guvenli Mod | 0.871 | 1.000 | 0.500 |

## 7. Nihai Yorum ve Oneriler

- Izleme penceresinde 26 olay incelenmis, 17 olay saldiri/anomali olarak degerlendirilmistir.
- En baskin tehditler: lane_deviation (7), sudden_brake (4), dos (3), sensor_noise (2), gps_spoofing (1).
- Nihai karar **Acil Guvenli Mod** olarak atanmistir; bu karar CARLA davranis/sensor katmani ve fusion karar katmanindaki kritik bulgularla desteklenmektedir.
- Onerilen operasyonel aksiyon: araci kontrollu sekilde kisitli/guvenli davranisa almak, riskli manevralari engellemek, telemetriyi kaydetmek ve insan operator incelemesine aktarmak.
- CIC ve gorsel katman bu pencerede esik ustu bulgu uretmedigi icin ana risk kaynagi davranis/sensor anomalileri olarak yorumlanmalidir.

## 8. Ollama Durumu

Ollama yorumu istenmedi.

## 9. Notlar

- Bu rapor karar destek amaclidir; nihai operasyon karari sistem politikasi ve insan denetimiyle birlikte verilmelidir.
- Safe mode karari CIC, CARLA, nuScenes gorsel tutarlilik ve fusion karar katmaninin birlikte degerlendirilmesiyle uretilmistir.
- Kritik siniflarda temkinli karar verilmesi, otonom arac guvenligi acisindan tercih edilen davranistir.
