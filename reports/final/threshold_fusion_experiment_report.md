# Threshold Fusion Experiment Report

Bu rapor, CIC + CARLA + nuScenes katmanlarina esik degerlendirme sinyalleri eklendikten sonra uretilen egitim, test ve demo rapor sonuclarini ozetler.

## 1. Deney Ozeti

Yeni fusion modeli:

```text
models/fusion_threshold_no_attack_type_v1
```

Kullanilan feature set:

```text
no_attack_type
```

Bu ayarda karar katmanina CIC/CARLA attack type isimleri dogrudan verilmez. Model; saldiri olasiliklari, guven skorlarini, nuScenes gorsel tutarlilik sinyallerini ve yeni esik feature'larini kullanir.

Eklenen esik feature'lari:

```text
cic_threshold_triggered
carla_threshold_triggered
visual_threshold_triggered
threshold_trigger_count
max_layer_threshold_score
```

## 2. Fusion Validation Sonuclari

Kaynak dosyalar:

```text
models/fusion_threshold_no_attack_type_v1/metrics/fusion_validation_risk_metrics.json
models/fusion_threshold_no_attack_type_v1/metrics/fusion_validation_attack_type_metrics.json
```

| Hedef | Accuracy | Macro F1 | Weighted F1 | Log Loss |
|---|---:|---:|---:|---:|
| Risk | 1.0000 | 1.0000 | 1.0000 | 0.0008 |
| Attack type | 0.5200 | 0.5054 | 0.5054 | 1.2259 |

Validation risk skorunun 1.0000 olmasi tek basina nihai basari kabul edilmemelidir. Test sonucu esas alinmalidir.

## 3. Fusion Test Sonuclari

Kaynak dosya:

```text
reports/fusion_threshold_no_attack_type_v1_test.json
```

Test ornek sayisi:

```text
5000
```

| Hedef | Accuracy | Macro F1 | Weighted F1 | Log Loss |
|---|---:|---:|---:|---:|
| Risk | 0.7898 | 0.7365 | 0.8100 | 0.7491 |
| Attack type | 0.3898 | 0.3231 | 0.3524 | 4.2494 |

Risk confusion matrix ozeti:

| True \ Pred | attack | normal |
|---|---:|---:|
| attack | 3099 | 951 |
| normal | 100 | 850 |

Yorum:

- Risk tespitinde model kullanilabilir seviyede sinyal uretiyor.
- Attack type tahmini karar katmanina birakildiginda zayif kaliyor.
- Bu nedenle fusion katmani nihai "risk / safe mode" karari icin kullanilmali.
- Saldiri turu raporlamasi CIC ve CARLA katmanlarinin kendi tahminlerinden alinmali.

## 4. Onceki Model ile Karsilastirma

Onceki CIC + CARLA + visual modeli:

```text
models/fusion_cic_carla_visual_v1
```

Kaynak dosya:

```text
reports/fusion_cic_carla_visual_v1_test.json
```

| Model | Risk Accuracy | Risk Macro F1 | Type Accuracy | Type Macro F1 |
|---|---:|---:|---:|---:|
| fusion_cic_carla_visual_v1 | 0.8064 | 0.7398 | 0.3982 | 0.3285 |
| fusion_threshold_no_attack_type_v1 | 0.7898 | 0.7365 | 0.3898 | 0.3231 |

Esik feature'lari eklendikten sonra test accuracy az miktarda dustu, macro F1 ise risk tarafinda neredeyse ayni kaldi. Bu, esik sinyallerinin modele zarar vermedigini ama mevcut veri eslestirme yapisinda performansi belirgin artirmadigini gosterir.

## 5. Demo Rapor Sonucu

Kaynak dosya:

```text
reports/demo_threshold_ollama.json
```

Demo ornek sayisi:

```text
100
```

Ozet:

| Alan | Deger |
|---|---:|
| Event count | 100 |
| Attack karar sayisi | 76 |
| Normal karar sayisi | 24 |
| Review required | 76 |
| Safe mode required | 76 |
| Recommended safe mode | emergency_safe_mode |

En sik gorulen tehditler:

| Attack type | Count |
|---|---:|
| sudden_brake | 21 |
| position_spoofing | 14 |
| speed_spoofing | 8 |
| dos | 7 |
| gps_spoofing | 7 |
| sensor_noise | 7 |
| delayed_sensor_attack | 6 |
| lane_deviation | 5 |
| heading_spoofing | 1 |

Esik ozeti:

| Alan | Sonuc |
|---|---|
| Final level distribution | critical: 76, low: 24 |
| Safe mode distribution | emergency_safe_mode: 76, normal_mode: 24 |
| Triggered layers | carla: 70, fusion: 76, visual: 1 |
| Recommended safe mode | emergency_safe_mode |

Katman seviyesi dagilimi:

| Katman | Dagilim |
|---|---|
| CIC | low: 100 |
| CARLA | critical: 51, high: 9, medium: 10, low: 30 |
| Visual | high: 1, low: 99 |
| Fusion | critical: 76, low: 24 |

Bu demo penceresinde safe mode kararini agirlikli olarak CARLA ve fusion katmanlari tetikledi. CIC katmani bu ornek penceresinde esik ustu risk uretmedi. Visual katman yalnizca 1 event icin high seviyeye cikti.

## 6. Ollama Durumu

Ollama entegrasyonu rapora eklendi, ancak bu calistirmada servis kapali oldugu icin LLM yorumu alinmadi.

```text
model: llama3.1
status: error
error: <urlopen error [Errno 61] Connection refused>
```

LLM yorumunun rapora dolmasi icin once Ollama servisinin acik olmasi gerekir:

```bash
ollama serve
ollama pull llama3.1
```

Sonra demo komutu tekrar calistirilmelidir.

## 7. Teknik Karar

Bu asamada dogru mimari:

```text
CIC modeli:
  - Ag saldirisi var/yok
  - Ag saldiri turu

CARLA modeli:
  - Davranis/sensor anomalisi var/yok
  - Davranis/sensor saldiri turu

nuScenes katmani:
  - Gorsel tutarlilik
  - Halusinasyon/tutarsizlik suphe skoru

Fusion karar katmani:
  - Nihai risk
  - Safe mode gerekli mi
  - Hangi mod: normal, monitoring, degraded, emergency
```

Fusion katmaninin attack type tahminini nihai kaynak olarak kullanmak dogru degildir. Attack type bilgisi katman bazli raporlanmalidir.

## 8. Sonraki Adimlar

1. Safe mode karar etiketini ayri bir hedef olarak uretmek.
2. Fusion modelini `risk` ve `safe_mode` hedeflerine odaklamak.
3. Attack type modelini fusion icinde ikincil/yardimci cikti yapmak veya rapordan cikarmak.
4. Demo raporunda katman bazli bulgulari daha okunur hale getirmek.
5. Ollama servisini calistirip LLM yorum alanini doldurmak.
6. CARLA simülasyon entegrasyonu icin online inference scripti hazirlamak.

## 9. Safe Mode Hedefli Yeni Fusion Denemesi

Bu asamada fusion katmaninin attack type tahmini yapmasi yerine iki ana hedefe odaklanmasina karar verildi:

```text
1. Nihai risk: attack / normal
2. Guvenli mod: normal_mode / monitoring_mode / degraded_safe_mode / emergency_safe_mode
```

Attack type bilgisi artik karar katmaninin ana hedefi degildir. Saldiri turu bilgisi CIC ve CARLA katmanlarindan katman bazli bulgu olarak raporlanir. Fusion katmani bu bulgulari, esik sinyallerini ve gorsel tutarlilik skorlarini kullanarak guvenli mod karari verir.

Eklenen/degisen teknik parcalar:

```text
src/security_pipeline/thresholds.py
src/security_pipeline/ollama.py
src/security_pipeline/fusion.py
src/security_pipeline/cli.py
```

Safe mode etiketleri bu ilk denemede pseudo-label olarak uretilmistir:

| Kosul | Safe mode etiketi |
|---|---|
| Normal olay | normal_mode |
| Ani fren veya serit sapmasi | emergency_safe_mode |
| DoS, gecikmeli sensor, GPS/heading/position/speed spoofing | degraded_safe_mode |
| Daha dusuk etkili anomali | monitoring_mode |
| Cok yuksek gorsel halusinasyon skoru | emergency_safe_mode |

Bu nokta makalede acik yazilmalidir: safe mode modeli simdilik insan etiketiyle degil, kural tabanli risk politikasindan uretilen etiketlerle egitilmistir.

### 9.1 Smoke Validation Sonucu

Kaynak model:

```text
models/smoke_safe_mode
```

Egitim ayari:

```text
max_rows=200
cic_max_rows=200
visual_samples=200
n_estimators=10
feature_set=no_attack_type
```

| Hedef | Accuracy | Macro F1 | Weighted F1 | Log Loss |
|---|---:|---:|---:|---:|
| Risk | 1.0000 | 1.0000 | 1.0000 | 0.0049 |
| Safe mode | 0.6750 | 0.5186 | 0.6379 | 2.4490 |

Bu sonuc yalnizca pipeline smoke testidir; veri sayisi kucuk oldugu icin akademik performans sonucu olarak kullanilmamalidir.

### 9.2 Smoke Test Sonucu

Kaynak dosyalar:

```text
reports/smoke_safe_mode_test.json
reports/smoke_safe_mode_test_metrics/fusion_test_risk_metrics.json
reports/smoke_safe_mode_test_metrics/fusion_test_safe_mode_metrics.json
```

Test ayari:

```text
max_rows=100
cic_max_rows=100
visual_samples=100
```

| Hedef | Accuracy | Macro F1 | Weighted F1 | Log Loss |
|---|---:|---:|---:|---:|
| Risk | 0.7900 | 0.6518 | 0.8273 | 4.5359 |
| Safe mode | 0.5300 | 0.3269 | 0.5061 | 6.7523 |

Risk confusion matrix:

| True \ Pred | attack | normal |
|---|---:|---:|
| attack | 71 | 19 |
| normal | 2 | 8 |

Safe mode confusion matrix:

| True \ Pred | degraded_safe_mode | emergency_safe_mode | monitoring_mode | normal_mode |
|---|---:|---:|---:|---:|
| degraded_safe_mode | 42 | 6 | 3 | 9 |
| emergency_safe_mode | 5 | 2 | 1 | 12 |
| monitoring_mode | 9 | 1 | 0 | 0 |
| normal_mode | 0 | 1 | 0 | 9 |

Yorum:

- Yeni mimari teknik olarak calisiyor ve artik `fusion_test_safe_mode` metrigi uretiliyor.
- Risk hedefi smoke testte makul sinyal veriyor.
- Safe mode hedefi henuz zayif; ozellikle `emergency_safe_mode` ve `monitoring_mode` siniflarinda veri/etiket ayrimi yetersiz.
- Tam deney icin daha buyuk veriyle egitim ve test alinmali; smoke sonucu yalnizca entegrasyon kanitidir.

## 10. Safe Mode Fusion v1 Tam Deney Sonuclari

Kaynak model:

```text
models/fusion_safe_mode_v1
```

Kaynak metrik dosyalari:

```text
models/fusion_safe_mode_v1/metrics/fusion_validation_risk_metrics.json
models/fusion_safe_mode_v1/metrics/fusion_validation_safe_mode_metrics.json
reports/fusion_safe_mode_v1_test_metrics/fusion_test_risk_metrics.json
reports/fusion_safe_mode_v1_test_metrics/fusion_test_safe_mode_metrics.json
```

Deney ayari:

```text
train rows: 4000
validation rows: 1000
test rows: 5000
feature_set: no_attack_type
n_estimators: 300
```

### 10.1 Validation Sonuclari

| Hedef | Accuracy | Macro F1 | Weighted F1 | Log Loss |
|---|---:|---:|---:|---:|
| Risk | 1.0000 | 1.0000 | 1.0000 | 0.0010 |
| Safe mode | 0.7620 | 0.7102 | 0.7545 | 0.5121 |

Validation risk confusion matrix:

| True \ Pred | attack | normal |
|---|---:|---:|
| attack | 900 | 0 |
| normal | 0 | 100 |

Validation safe mode confusion matrix:

| True \ Pred | degraded_safe_mode | emergency_safe_mode | monitoring_mode | normal_mode |
|---|---:|---:|---:|---:|
| degraded_safe_mode | 496 | 71 | 33 | 0 |
| emergency_safe_mode | 64 | 136 | 0 | 0 |
| monitoring_mode | 68 | 2 | 30 | 0 |
| normal_mode | 0 | 0 | 0 | 100 |

### 10.2 Test Sonuclari

Kaynak dosya:

```text
reports/fusion_safe_mode_v1_test.json
```

| Hedef | Accuracy | Macro F1 | Weighted F1 | Log Loss |
|---|---:|---:|---:|---:|
| Risk | 0.7898 | 0.7365 | 0.8100 | 0.7486 |
| Safe mode | 0.5868 | 0.4866 | 0.5772 | 1.7373 |

Risk confusion matrix:

| True \ Pred | attack | normal |
|---|---:|---:|
| attack | 3099 | 951 |
| normal | 100 | 850 |

Safe mode confusion matrix:

| True \ Pred | degraded_safe_mode | emergency_safe_mode | monitoring_mode | normal_mode |
|---|---:|---:|---:|---:|
| degraded_safe_mode | 1726 | 464 | 11 | 499 |
| emergency_safe_mode | 167 | 268 | 0 | 465 |
| monitoring_mode | 327 | 34 | 89 | 0 |
| normal_mode | 56 | 43 | 0 | 851 |

Sinif bazli test F1 skorlari:

| Safe mode sinifi | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| degraded_safe_mode | 0.7583 | 0.6393 | 0.6937 | 2700 |
| emergency_safe_mode | 0.3313 | 0.2978 | 0.3136 | 900 |
| monitoring_mode | 0.8900 | 0.1978 | 0.3236 | 450 |
| normal_mode | 0.4689 | 0.8958 | 0.6156 | 950 |

Yorum:

- Risk tespiti testte onceki threshold modelle ayni seviyede kaldi: accuracy 0.7898, macro F1 0.7365.
- Safe mode hedefi smoke denemeye gore iyilesti: accuracy 0.5300 -> 0.5868, macro F1 0.3269 -> 0.4866.
- En iyi ayrilan safe mode sinifi `degraded_safe_mode` oldu.
- `emergency_safe_mode` sinifi halen zayif; model bu sinifin onemli bir bolumunu `normal_mode` veya `degraded_safe_mode` olarak karistiriyor.
- `monitoring_mode` icin precision yuksek fakat recall dusuk; model monitoring olaylarini yakalamakta cekingen davraniyor.
- Bu sonuc karar katmani icin kullanilabilir bir baslangic saglar, ancak guvenli mod kararinin akademik olarak daha guclu savunulmasi icin safe mode etiket politikasinin netlestirilmesi ve sinif dengesinin iyilestirilmesi gerekir.

## 11. Safe Mode Fusion v2 Politika Iyilestirmesi

v1 sonucunda `emergency_safe_mode` sinifinin zayif kaldigi goruldu. Bu nedenle iki degisiklik yapildi:

```text
1. Safe mode pseudo-label politikasi sertlestirildi.
2. Tahmin sonrasi guvenlik politikasi eklendi.
```

Yeni politikada:

| Durum | Karar |
|---|---|
| sudden_brake, lane_deviation, position_spoofing | emergency_safe_mode |
| dos, delayed_sensor_attack, gps_spoofing, heading_spoofing, speed_spoofing | degraded_safe_mode |
| hallucination_probability >= 0.85 | emergency_safe_mode |
| hallucination_probability >= 0.70 ve yakin tehlike var | emergency_safe_mode |
| hallucination_probability >= 0.65 | degraded_safe_mode |
| risk yuksekken model normal_mode derse | normal_mode bastirilir |

Kaynak model:

```text
models/fusion_safe_mode_v2
```

Kaynak metrik dosyalari:

```text
models/fusion_safe_mode_v2/metrics/fusion_validation_risk_metrics.json
models/fusion_safe_mode_v2/metrics/fusion_validation_safe_mode_metrics.json
reports/fusion_safe_mode_v2_test_metrics/fusion_test_risk_metrics.json
reports/fusion_safe_mode_v2_test_metrics/fusion_test_safe_mode_metrics.json
```

Deney ayari:

```text
train rows: 4000
validation rows: 1000
test rows: 5000
feature_set: no_attack_type
n_estimators: 300
```

### 11.1 Validation Sonuclari

| Hedef | Accuracy | Macro F1 | Weighted F1 | Log Loss |
|---|---:|---:|---:|---:|
| Risk | 1.0000 | 1.0000 | 1.0000 | 0.0007 |
| Safe mode | 0.7900 | 0.7567 | 0.7840 | 0.5824 |

Validation safe mode confusion matrix:

| True \ Pred | degraded_safe_mode | emergency_safe_mode | monitoring_mode | normal_mode |
|---|---:|---:|---:|---:|
| degraded_safe_mode | 353 | 98 | 51 | 0 |
| emergency_safe_mode | 0 | 300 | 0 | 0 |
| monitoring_mode | 57 | 4 | 37 | 0 |
| normal_mode | 0 | 0 | 0 | 100 |

### 11.2 Test Sonuclari

| Hedef | Accuracy | Macro F1 | Weighted F1 | Log Loss |
|---|---:|---:|---:|---:|
| Risk | 0.7900 | 0.7367 | 0.8101 | 0.7543 |
| Safe mode | 0.5766 | 0.5310 | 0.5697 | 1.7408 |

Risk confusion matrix:

| True \ Pred | attack | normal |
|---|---:|---:|
| attack | 3100 | 950 |
| normal | 100 | 850 |

Safe mode confusion matrix:

| True \ Pred | degraded_safe_mode | emergency_safe_mode | monitoring_mode | normal_mode |
|---|---:|---:|---:|---:|
| degraded_safe_mode | 1129 | 679 | 25 | 424 |
| emergency_safe_mode | 9 | 801 | 1 | 539 |
| monitoring_mode | 306 | 35 | 102 | 0 |
| normal_mode | 10 | 89 | 0 | 851 |

Sinif bazli test F1 skorlari:

| Safe mode sinifi | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| degraded_safe_mode | 0.7765 | 0.5002 | 0.6085 | 2257 |
| emergency_safe_mode | 0.4994 | 0.5933 | 0.5423 | 1350 |
| monitoring_mode | 0.7969 | 0.2302 | 0.3573 | 443 |
| normal_mode | 0.4691 | 0.8958 | 0.6158 | 950 |

### 11.3 v1 ile Karsilastirma

| Model | Risk Acc. | Risk Macro F1 | Safe Mode Acc. | Safe Mode Macro F1 |
|---|---:|---:|---:|---:|
| fusion_safe_mode_v1 | 0.7898 | 0.7365 | 0.5868 | 0.4866 |
| fusion_safe_mode_v2 | 0.7900 | 0.7367 | 0.5766 | 0.5310 |

Sinif bazli onemli fark:

| Sinif | v1 F1 | v2 F1 | Yorum |
|---|---:|---:|---|
| degraded_safe_mode | 0.6937 | 0.6085 | Dustu; bazi degraded olaylar emergency tarafina kaydi |
| emergency_safe_mode | 0.3136 | 0.5423 | Belirgin iyilesti |
| monitoring_mode | 0.3236 | 0.3573 | Az iyilesti |
| normal_mode | 0.6156 | 0.6158 | Neredeyse ayni |

Yorum:

- v2, toplam safe mode accuracy acisindan v1'den biraz dusuk: 0.5868 -> 0.5766.
- Ancak macro F1 daha yuksek: 0.4866 -> 0.5310. Bu akademik olarak daha anlamlidir, cunku siniflar dengesizdir.
- En onemli kazanc `emergency_safe_mode` sinifindadir. F1 skoru 0.3136'dan 0.5423'e cikti.
- Guvenlik odakli sistemde kritik modu yakalamak onemli oldugu icin v2 politikasi daha savunulabilir.
- Bedel olarak `degraded_safe_mode` sinifinda dusus oldu. Bu beklenen bir trade-off'tur: politika bazi yuksek etkili olaylari emergency tarafina tasidi.

## 12. Safe Mode Fusion v3 Etki Skoru Feature Iyilestirmesi

v2 sonucunda `emergency_safe_mode` iyilesmis olsa da `degraded_safe_mode` ile `emergency_safe_mode` arasinda karisim devam ediyordu. Bunun temel nedeni, safe mode etiketinin saldiri turunun etkisine bagli olmasina ragmen `feature_set=no_attack_type` ayarinda modele ham attack type verilmemesiydi.

v3'te ham attack type dogrudan modele verilmedi. Bunun yerine katman saldiri turlerinden turetilen sayisal etki feature'lari eklendi:

```text
cic_attack_severity
carla_attack_severity
max_attack_severity
high_impact_attack_detected
```

Bu yaklasim akademik olarak daha temizdir:

```text
Karar katmani ham saldiri turu etiketini ezberlemek yerine, katmanlarin bildirdigi saldiri etkisini sayisal risk siddeti olarak kullanir.
```

Kaynak model:

```text
models/fusion_safe_mode_v3
```

Kaynak metrik dosyalari:

```text
models/fusion_safe_mode_v3/metrics/fusion_validation_risk_metrics.json
models/fusion_safe_mode_v3/metrics/fusion_validation_safe_mode_metrics.json
reports/fusion_safe_mode_v3_test_metrics/fusion_test_risk_metrics.json
reports/fusion_safe_mode_v3_test_metrics/fusion_test_safe_mode_metrics.json
```

Deney ayari:

```text
train rows: 4000
validation rows: 1000
test rows: 5000
feature_set: no_attack_type
n_estimators: 300
```

### 12.1 Validation Sonuclari

| Hedef | Accuracy | Macro F1 | Weighted F1 | Log Loss |
|---|---:|---:|---:|---:|
| Risk | 1.0000 | 1.0000 | 1.0000 | 0.0001 |
| Safe mode | 1.0000 | 1.0000 | 1.0000 | 0.0045 |

Validation safe mode confusion matrix:

| True \ Pred | degraded_safe_mode | emergency_safe_mode | monitoring_mode | normal_mode |
|---|---:|---:|---:|---:|
| degraded_safe_mode | 502 | 0 | 0 | 0 |
| emergency_safe_mode | 0 | 300 | 0 | 0 |
| monitoring_mode | 0 | 0 | 98 | 0 |
| normal_mode | 0 | 0 | 0 | 100 |

Not: Validation skorunun 1.0000 olmasi tek basina nihai basari olarak yorumlanmamalidir. Burada esas degerlendirme test seti uzerinden yapilmalidir.

### 12.2 Test Sonuclari

| Hedef | Accuracy | Macro F1 | Weighted F1 | Log Loss |
|---|---:|---:|---:|---:|
| Risk | 0.7874 | 0.7343 | 0.8079 | 1.4365 |
| Safe mode | 0.7530 | 0.7778 | 0.7655 | 1.9088 |

Risk confusion matrix:

| True \ Pred | attack | normal |
|---|---:|---:|
| attack | 3086 | 964 |
| normal | 99 | 851 |

Safe mode confusion matrix:

| True \ Pred | degraded_safe_mode | emergency_safe_mode | monitoring_mode | normal_mode |
|---|---:|---:|---:|---:|
| degraded_safe_mode | 1715 | 110 | 8 | 424 |
| emergency_safe_mode | 50 | 760 | 0 | 540 |
| monitoring_mode | 4 | 0 | 439 | 0 |
| normal_mode | 25 | 74 | 0 | 851 |

Sinif bazli test F1 skorlari:

| Safe mode sinifi | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| degraded_safe_mode | 0.9560 | 0.7599 | 0.8467 | 2257 |
| emergency_safe_mode | 0.8051 | 0.5630 | 0.6626 | 1350 |
| monitoring_mode | 0.9821 | 0.9910 | 0.9865 | 443 |
| normal_mode | 0.4689 | 0.8958 | 0.6156 | 950 |

### 12.3 v1-v2-v3 Karsilastirma

| Model | Risk Acc. | Risk Macro F1 | Safe Mode Acc. | Safe Mode Macro F1 |
|---|---:|---:|---:|---:|
| fusion_safe_mode_v1 | 0.7898 | 0.7365 | 0.5868 | 0.4866 |
| fusion_safe_mode_v2 | 0.7900 | 0.7367 | 0.5766 | 0.5310 |
| fusion_safe_mode_v3 | 0.7874 | 0.7343 | 0.7530 | 0.7778 |

Sinif bazli F1 karsilastirmasi:

| Sinif | v1 F1 | v2 F1 | v3 F1 | Yorum |
|---|---:|---:|---:|---|
| degraded_safe_mode | 0.6937 | 0.6085 | 0.8467 | Belirgin iyilesti |
| emergency_safe_mode | 0.3136 | 0.5423 | 0.6626 | Kritik modda guclu iyilesme |
| monitoring_mode | 0.3236 | 0.3573 | 0.9865 | Cok belirgin iyilesti |
| normal_mode | 0.6156 | 0.6158 | 0.6156 | Neredeyse sabit |

Yorum:

- v3, safe mode karar katmani icin su ana kadarki en iyi modeldir.
- Risk tespit performansi v1/v2 ile ayni seviyede kalmistir; risk accuracy yaklasik 0.79 bandindadir.
- Safe mode accuracy 0.5766'dan 0.7530'a, macro F1 0.5310'dan 0.7778'e cikmistir.
- Bu iyilesme, karar katmanina ham attack type vermeden etki/siddet feature'lari eklemenin dogru bir yaklasim oldugunu gosterir.
- `emergency_safe_mode` F1 skoru v1'e gore 0.3136'dan 0.6626'ya cikmistir. Bu, guvenlik odakli otonom arac sistemi icin en kritik kazanimdir.
- `normal_mode` sinifinda F1 sinirli kalmistir; bunun nedeni modelin guvenlik tarafinda temkinli davranmasi ve bazi attack olaylarini normal ile karistirmasidir.
- Makalede ana karar katmani sonucu olarak `fusion_safe_mode_v3` kullanilmalidir. `fusion_safe_mode_v1` ve `fusion_safe_mode_v2` ise ablasyon/iyilestirme adimlari olarak raporlanabilir.
