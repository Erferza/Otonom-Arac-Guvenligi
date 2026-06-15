# NPC Hallucination Test - Mismatched CIC/CARLA Attacks

## 0. NPC Scenario Fazlari (Mismatched CIC/CARLA Attacks)

| Faz | Sure (tick) | CARLA | CIC | Beklenen safe mode | Amac |
|---|---:|---|---|---|---|
| npc_baseline_normal | 28 | normal | Benign | normal_mode | Establish clean baseline with NPC traffic present. |
| npc_mitm_smooth_drive | 26 | normal | mitm | monitoring_mode | MITM network attack while vehicle drives smoothly (CIC anomaly, CARLA normal). |
| npc_dos_sudden_brake | 30 | sudden_brake | dos | degraded_safe_mode | DDoS attack coupled with hard emergency braking. |
| npc_scanning_lane_deviation | 32 | lane_deviation | scanning | emergency_safe_mode | Port scanning reconnaissance with lane control hijacking. |
| npc_dos_speed_spoof | 28 | speed_spoofing | dos | emergency_safe_mode | DDoS attack with speed sensor spoofing causing false velocity readings. |
| npc_scanning_delayed_sensor | 24 | delayed_sensor_attack | scanning | emergency_safe_mode | Coordinated port scanning + sensor delay attack in congested NPC scenario. |

## Test Metrikleri

| Metrik | Risk | Safe mode |
|---|---:|---:|
| Accuracy | 0.706 | 0.618 |
| Macro F1 | 0.622 | 0.393 |
## Gorsel Karsilastirma (NPC Trafik Ile)

| # | Faz | Gorsel p | Kamera on gorunen aktor | NPC count | Sensor front | Fren | Aciklama | Image |
|---|---|---:|---:|---:|---:|---:|---|---|
| 11 | npc_dos_sudden_brake | 0.820 | 0 | 0 | 44.6 | 1.00 | Ani fren icin gorselde yakin tehlike yok; anomalilik olasiligi yuksek. | images/007790_npc_dos_sudden_brake.png |
| 12 | npc_dos_sudden_brake | 0.820 | 0 | 0 | 44.0 | 1.00 | Ani fren icin gorselde yakin tehlike yok; anomalilik olasiligi yuksek. | images/007795_npc_dos_sudden_brake.png |
| 13 | npc_dos_sudden_brake | 0.820 | 0 | 0 | 43.6 | 1.00 | Ani fren icin gorselde yakin tehlike yok; anomalilik olasiligi yuksek. | images/007800_npc_dos_sudden_brake.png |
| 14 | npc_dos_sudden_brake | 0.820 | 0 | 0 | 44.2 | 1.00 | Ani fren icin gorselde yakin tehlike yok; anomalilik olasiligi yuksek. | images/007805_npc_dos_sudden_brake.png |
| 15 | npc_dos_sudden_brake | 0.820 | 0 | 0 | 45.0 | 1.00 | Ani fren icin gorselde yakin tehlike yok; anomalilik olasiligi yuksek. | images/007810_npc_dos_sudden_brake.png |
| 16 | npc_dos_sudden_brake | 0.820 | 0 | 0 | 45.8 | 1.00 | Ani fren icin gorselde yakin tehlike yok; anomalilik olasiligi yuksek. | images/007815_npc_dos_sudden_brake.png |
| 24 | npc_dos_speed_spoof | 0.500 | 0 | 0 | 51.8 | 0.00 | Gorsel katman bu saldiri turu icin destekleyici sinyal olarak kullanildi. | images/007855_npc_dos_speed_spoof.png |
| 25 | npc_dos_speed_spoof | 0.500 | 0 | 0 | 52.1 | 0.00 | Gorsel katman bu saldiri turu icin destekleyici sinyal olarak kullanildi. | images/007860_npc_dos_speed_spoof.png |
| 26 | npc_dos_speed_spoof | 0.500 | 0 | 0 | 52.1 | 0.00 | Gorsel katman bu saldiri turu icin destekleyici sinyal olarak kullanildi. | images/007865_npc_dos_speed_spoof.png |
| 27 | npc_dos_speed_spoof | 0.500 | 0 | 0 | 52.2 | 0.00 | Gorsel katman bu saldiri turu icin destekleyici sinyal olarak kullanildi. | images/007870_npc_dos_speed_spoof.png |

# Otonom Arac Guvenlik Izleme Raporu

## 1. Yonetici Ozeti

Bu rapor 34 olaylik izleme penceresi icin uretilmistir. Sistem 22 olayda saldiri/anomali, 12 olayda normal durum karari vermistir. Nihai guvenli mod onerisi: **Acil Guvenli Mod**.

| Metrik | Deger |
|---|---:|
| Toplam olay | 34 |
| Attack/anomali karari | 22 (64.7%) |
| Normal karar | 12 (35.3%) |
| Insan incelemesi gereken olay | 22 (64.7%) |
| Guvenli mod gerektiren olay | 30 (88.2%) |
| Onerilen guvenli mod | Acil Guvenli Mod |

## 2. Nihai Karar

Sistem **Acil Guvenli Mod** onermektedir. Bu karar, izleme penceresinde 27 kritik, 3 yuksek ve 0 orta seviye bulgu olusmasi nedeniyle verilmistir. Aracin operasyonel riski yuksek kabul edilmeli, hiz/rota kontrolu kisitlanmali ve guvenli durus veya kontrollu devralma senaryosu uygulanmalidir.

## 3. Katman Bazli Bulgular

| Katman | Tetiklenen olay | Seviye dagilimi | Yorum |
|---|---:|---|---|
| CIC ag katmani | 28 | critical: 26, high: 1, low: 6, medium: 1 | Ag katmani bulgulari izlenmistir. |
| CARLA davranis/sensor katmani | 22 | critical: 7, high: 8, low: 12, medium: 7 | Davranis/sensor anomalileri karar uzerinde belirleyici oldu. |
| nuScenes gorsel tutarlilik katmani | 6 | high: 6, low: 18, medium: 10 | Gorsel tutarlilik sinyali izlenmistir. |
| Fusion karar katmani | 22 | critical: 15, high: 7, low: 12 | Katman sinyallerini birlestirerek nihai risk kararini destekledi. |

## 4. Tehdit Sikliklari

| Tehdit/anomali turu | Olay sayisi | Oran |
|---|---:|---:|
| position_spoofing | 10 | 29.4% |
| sudden_brake | 5 | 14.7% |
| speed_spoofing | 5 | 14.7% |
| lane_deviation | 1 | 2.9% |
| sensor_noise | 1 | 2.9% |

## 5. Guvenli Mod Dagilimi

| Sinif | Olay sayisi | Oran |
|---|---:|---:|
| Kisitli Guvenli Mod | 3 | 8.8% |
| Acil Guvenli Mod | 27 | 79.4% |
| Normal Mod | 4 | 11.8% |

## 6. Oncelikli Olay Ornekleri

| # | Zaman | Risk | Saldiri turu | Safe mode | CARLA p | CIC p | Gorsel p |
|---:|---:|---|---|---|---:|---:|---:|
| 3 | 54.43497933074832 | attack | position_spoofing | Acil Guvenli Mod | 0.613 | 0.004 | 0.120 |
| 4 | 54.68497933447361 | attack | position_spoofing | Acil Guvenli Mod | 0.682 | 0.000 | 0.120 |
| 6 | 55.18497934192419 | attack | position_spoofing | Acil Guvenli Mod | 0.758 | 0.916 | 0.120 |
| 7 | 55.43497934564948 | attack | position_spoofing | Acil Guvenli Mod | 0.679 | 1.000 | 0.120 |
| 8 | 55.68497934937477 | attack | position_spoofing | Acil Guvenli Mod | 0.748 | 0.790 | 0.120 |
| 9 | 55.93497935310006 | attack | lane_deviation | Acil Guvenli Mod | 0.771 | 0.958 | 0.120 |
| 10 | 56.18497935682535 | attack | position_spoofing | Acil Guvenli Mod | 0.835 | 0.944 | 0.120 |
| 11 | 56.43497936055064 | attack | sudden_brake | Acil Guvenli Mod | 0.783 | 0.983 | 0.820 |
| 12 | 56.68497936427593 | attack | sudden_brake | Acil Guvenli Mod | 0.862 | 1.000 | 0.820 |
| 13 | 56.93497936800122 | attack | sudden_brake | Acil Guvenli Mod | 0.832 | 1.000 | 0.820 |
| 14 | 57.18497937172651 | attack | sudden_brake | Acil Guvenli Mod | 0.811 | 0.842 | 0.820 |
| 15 | 57.4349793754518 | attack | sudden_brake | Acil Guvenli Mod | 0.807 | 0.992 | 0.820 |

## 7. Nihai Yorum ve Oneriler

- Izleme penceresinde 34 olay incelenmis, 22 olay saldiri/anomali olarak degerlendirilmistir.
- En baskin tehditler: position_spoofing (10), sudden_brake (5), speed_spoofing (5), lane_deviation (1), sensor_noise (1).
- Nihai karar **Acil Guvenli Mod** olarak atanmistir; bu karar CARLA davranis/sensor katmani ve fusion karar katmanindaki kritik bulgularla desteklenmektedir.
- Onerilen operasyonel aksiyon: araci kontrollu sekilde kisitli/guvenli davranisa almak, riskli manevralari engellemek, telemetriyi kaydetmek ve insan operator incelemesine aktarmak.
- CIC ve gorsel katman bu pencerede esik ustu bulgu uretmedigi icin ana risk kaynagi davranis/sensor anomalileri olarak yorumlanmalidir.

## 8. Ollama Durumu

Ollama yorumu istenmedi.

## 9. Notlar

- Bu rapor karar destek amaclidir; nihai operasyon karari sistem politikasi ve insan denetimiyle birlikte verilmelidir.
- Safe mode karari CIC, CARLA, nuScenes gorsel tutarlilik ve fusion karar katmaninin birlikte degerlendirilmesiyle uretilmistir.
- Kritik siniflarda temkinli karar verilmesi, otonom arac guvenligi acisindan tercih edilen davranistir.
