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

## 7. LLM Yorumu

This is a JSON object containing an array of objects, each representing a detection of potential attacks or threats. Here's a brief explanation of the structure and some key information from the provided data:

1. Each object in the array represents a separate event with the following properties:
   - `index`: A unique identifier for each event.
   - `timestamp`: The time when the event occurred, in Unix timestamp format.

2. For each event, there are three main sub-objects:
   - `cic_prediction`: Contains information about the attack prediction made by the CIC (Collaborative Intelligence Center) system. It includes:
     - `attack_probability`: The probability that an attack occurred.
     - `is_attack`: A boolean indicating whether an attack was detected or not.
     - `attack_type`: The type of attack predicted, if any (e.g., sudden brake).
     - `attack_type_confidence`: The confidence level of the attack prediction.

   - `carla_prediction`: Contains information about the attack prediction made by the CARLA (Car Learning to Act) system. It includes:
     - `attack_probability`: The probability that an attack occurred.
     - `is_attack`: A boolean indicating whether an attack was detected or not.
     - `attack_type`: The type of attack predicted, if any (e.g., sudden brake).
     - `attack_type_confidence`: The confidence level of the attack prediction.

   - `visual_consistency`: Contains information about the visual consistency check, which compares the current scene with previous ones to detect anomalies. It includes:
     - `hallucination_probability`: The probability that there is a hallucination or inconsistency in the current scene.
     - `explanation`: A brief explanation of the visual consistency check result.
     - `context`: Additional contextual information about the current scene, such as nearby objects and their distances.

3. There are also two other sub-objects for each event:
   - `decision`: Contains the final decision made by the system based on all available data. It includes:
     - `risk_score`: The overall risk score of the event.
     - `risk_level`: The level of risk associated with the event (e.g., low, medium, high).
     - `final_attack_type`: The final predicted attack type, if any.
     - `safe_mode`: The recommended safe mode to be activated in response to the event.
     - `safe_mode_confidence`: The confidence level of the safe mode recommendation.
     - `needs_human_review`: A boolean indicating whether human intervention is required for this event.
     - `reason`: An explanation of the final decision and safe mode recommendation.

   - `threshold_decision`: Contains information about the threshold-based decision-making process, which compares the predictions from CIC and CARLA with predefined thresholds to determine the overall risk level. It includes:
     - `cic`, `carla`, `visual`, and `fusion` sub-objects, each representing the result of the corresponding prediction compared against the threshold.
     - `final_level`: The overall risk level determined by the threshold-based decision-making process.
     - `safe_mode`: The recommended safe mode to be activated based on the final risk level.
     - `safe_mode_required`: A boolean indicating whether a safe mode should be activated for this event.
     - `reason`: An explanation of the threshold-based decision and safe mode recommendation.

## 8. Notlar

- Bu rapor karar destek amaclidir; nihai operasyon karari sistem politikasi ve insan denetimiyle birlikte verilmelidir.
- Safe mode karari CIC, CARLA, nuScenes gorsel tutarlilik ve fusion karar katmaninin birlikte degerlendirilmesiyle uretilmistir.
- Kritik siniflarda temkinli karar verilmesi, otonom arac guvenligi acisindan tercih edilen davranistir.
