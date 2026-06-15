# Katmanli Guvenlik Modeli Deney Raporu

Bu rapor, CIC-ToN-IoT, CARLA tabular ve nuScenes gorsel katmanlariyla kurulan hiyerarsik/fusion mimarisinin egitim sonuclarini ve leakage testini tek yerde ozetler.

## 1. Mimari Ozeti

Sistem dort ana katmandan olusur:

1. **CIC ag guvenligi katmani**
   - Girdi: CIC-ToN-IoT ag akis ozellikleri.
   - Model: Hiyerarsik ML.
   - Asama 1: binary saldiri var/yok.
   - Asama 2: saldiri varsa attack type tahmini.

2. **CARLA tabular sensor katmani**
   - Girdi: CARLA sensor, konum, hiz, fren, gecikme ve cevre tabular ozellikleri.
   - Model: Hiyerarsik ML.
   - Asama 1: binary saldiri var/yok.
   - Asama 2: saldiri varsa attack type tahmini.

3. **nuScenes gorsel katmani**
   - Girdi: nuScenes sahne metadata, annotation ve kamera dosya baglamlari.
   - Ciktilar: yakin obje sayisi, yakin arac sayisi, yaya/kirilgan yol kullanicisi sayisi, en yakin obje mesafesi, gorsel tutarlilik/anomali skoru.
   - Amac: sensor kararinin gorsel cevreyle uyumunu kontrol etmek. Ornek: sudden brake varsa yakinda arac/yaya/engel var mi?

4. **ML final karar/fusion katmani**
   - Girdi: CIC tahminleri, CARLA tahminleri ve nuScenes gorsel feature'lari.
   - Model: ML tabanli fusion.
   - Ciktilar: final risk karari, final attack type, human review ihtiyaci.

Karar akisi:

```text
CIC-ToN-IoT -> CIC ML prediction
CARLA tabular -> CARLA ML prediction
nuScenes -> visual consistency features
        -> ML Fusion Decision Layer
        -> final report
```

## 2. Ana Egitim Sonuclari

Asagidaki sonuclar `models/*/metrics` altindaki validation metriklerinden alinmistir.

| Katman | Accuracy | Macro F1 | Weighted F1 | Log Loss |
|---|---:|---:|---:|---:|
| CIC v2 binary | 0.9934 | 0.9923 | 0.9934 | 0.0261 |
| CIC v2 attack type | 0.6179 | 0.5397 | 0.6201 | 0.8173 |
| CARLA v2 binary | 1.0000 | 1.0000 | 1.0000 | 0.0059 |
| CARLA v2 attack type | 0.9765 | 0.9765 | 0.9765 | 0.2510 |
| Fusion v2 risk | 1.0000 | 1.0000 | 1.0000 | 0.0001 |
| Fusion v2 attack type | 1.0000 | 1.0000 | 1.0000 | 0.0036 |

### Ilk Yorum

Bu ilk tabloya bakildiginda CARLA ve fusion sonuclari cok yuksek gorunmektedir. Ancak bu degerler dogrudan nihai basari olarak yorumlanmamalidir. Ozellikle CARLA datasetinde saldiri uretiminden turemis bazi kolonlar modele cok guclu ipucu verebilir. Fusion katmaninda da CARLA modelinin tahmin ettigi `carla_attack_type` feature olarak verildiginde, final attack type tahmini kolaylasir.

Bu nedenle ek olarak leakage testi ve fusion ablation testi yapildi.

## 3. CIC Sonuclari

CIC tarafinda binary saldiri tespiti gucludur:

```text
CIC binary accuracy: 0.9934
CIC binary macro F1: 0.9923
```

Ancak attack type performansi daha zayiftir:

```text
CIC attack type accuracy: 0.6179
CIC attack type macro F1: 0.5397
```

Confusion matrix incelendiginde ozellikle su siniflarin birbirine karistigi gorulmektedir:

- `injection`
- `password`
- `xss`
- `scanning`

Bu daha gercekci bir zorluk seviyesine isaret eder. CIC tarafinda binary model guvenilir gorunurken, attack type modeli icin feature engineering, class balancing veya farkli model denemesi gereklidir.

Ilgili dosyalar:

- `models/cic_v2/metrics/cic_validation_binary_metrics.json`
- `models/cic_v2/metrics/cic_validation_binary_confusion_matrix.csv`
- `models/cic_v2/metrics/cic_validation_attack_type_metrics.json`
- `models/cic_v2/metrics/cic_validation_attack_type_confusion_matrix.csv`

## 4. CARLA Sonuclari

Ilk CARLA egitiminde sonuc cok yuksekti:

```text
CARLA v2 binary accuracy: 1.0000
CARLA v2 attack type accuracy: 0.9765
```

Bu ilk bakista cok iyi gorunse de leakage testi sonucunda bu skorlarin iyimser oldugu anlasildi.

### Leakage Testi: Baseline vs Strict

Leakage testinde iki CARLA modeli karsilastirildi:

- **Baseline CARLA:** Tum uygun tabular feature'lar kullanildi.
- **Strict/no-leakage CARLA:** Etiketi dogrudan veya dolayli ele verme riski yuksek kolonlar cikarildi.

Strict modda cikarilan ornek kolonlar:

```text
delayed_sensor_flag
heading_spoof_flag
hard_brake_flag
position_jump_flag
stale_packet_flag
speed_spoof_ratio
speed_spoof_offset
packet_delay_steps
sensor_delay_steps
gps_drift_magnitude
gps_drift_rate
position_jump_magnitude
missing_ratio
normal_subtype
gps_spoof_subtype
```

Leakage test sonucu:

| CARLA Model | Accuracy | Macro F1 | Weighted F1 | Log Loss |
|---|---:|---:|---:|---:|
| Baseline binary | 1.0000 | 1.0000 | 1.0000 | 0.0775 |
| Baseline attack type | 0.9726 | 0.9726 | 0.9726 | 0.3329 |
| Strict binary | 0.5838 | 0.5051 | 0.5051 | 0.7082 |
| Strict attack type | 0.7314 | 0.7327 | 0.7327 | 0.9836 |

### CARLA Yorumu

Bu sonuc onemli:

```text
Baseline binary: 1.0000 -> Strict binary: 0.5838
Baseline attack type: 0.9726 -> Strict attack type: 0.7314
```

Yani CARLA'daki ilk cok yuksek skorlarin onemli kismi leakage-prone feature'lardan kaynaklaniyor olabilir. Strict modelde attack type hala anlamli seviyede kalmistir, ancak binary performans ciddi sekilde dusmustur. Bu nedenle akademik/teknik raporda CARLA icin sadece baseline skorlarini vermek yaniltici olur.

Daha dogru ifade:

> CARLA baseline modeli cok yuksek performans vermistir; ancak leakage-prone feature'lar cikarildiginda performans dusmustur. Bu nedenle nihai degerlendirmede strict/no-leakage sonuclari esas alinmalidir.

## 5. nuScenes Gorsel Katmani

nuScenes katmani dogrudan attack type siniflandiricisi olarak kullanilmadi. Bu katman gorsel/cevre baglami uretti:

```text
visual_hallucination_probability
visual_close_object_count
visual_close_vehicle_count
visual_close_vulnerable_count
visual_nearest_object_m
visual_has_close_hazard
```

Ornek yorum:

- CARLA sudden brake diyorsa ve nuScenes sahnesinde yakinda arac/yaya/engel varsa, ani fren daha tutarli kabul edilir.
- CARLA sudden brake diyorsa ve gorsel baglamda yakin tehlike yoksa, anomalilik/halusinasyon olasiligi yukselir.

Ablation testinde sadece gorsel feature'larla attack type tahmini zayif kaldi:

```text
Fusion visual_only attack type accuracy: 0.3458
```

Bu beklenen bir durumdur. nuScenes katmani tek basina saldiri turunu cozmekten cok, sensor kararini baglamsal olarak destekleyen veya sorgulayan bir katmandir.

## 6. Fusion Ablation Sonuclari

Fusion katmaninda dort feature set test edildi:

| Fusion Feature Set | Risk Accuracy | Risk Macro F1 | Type Accuracy | Type Macro F1 |
|---|---:|---:|---:|---:|
| all | 0.9958 | 0.9882 | 0.9958 | 0.9958 |
| no_attack_type | 0.9958 | 0.9882 | 0.5042 | 0.4997 |
| visual_only | 0.9875 | 0.9632 | 0.3458 | 0.3412 |
| prediction_only | 0.9958 | 0.9882 | 0.9958 | 0.9958 |

Feature set anlamlari:

- **all:** CARLA prediction + CARLA attack type + visual feature'lar.
- **no_attack_type:** `carla_attack_type` ve `cic_attack_type` cikarildi.
- **visual_only:** sadece nuScenes gorsel feature'lari.
- **prediction_only:** sadece ara model tahminleri, gorsel feature yok.

### Fusion Yorumu

Fusion risk karari her durumda yuksek kaldi:

```text
all risk accuracy: 0.9958
no_attack_type risk accuracy: 0.9958
visual_only risk accuracy: 0.9875
prediction_only risk accuracy: 0.9958
```

Ancak attack type tarafinda kritik bir dusus var:

```text
all type accuracy: 0.9958
no_attack_type type accuracy: 0.5042
visual_only type accuracy: 0.3458
prediction_only type accuracy: 0.9958
```

Bu sunu gosterir:

> Fusion attack type basarisinin ana nedeni `carla_attack_type` feature'idir. Bu feature verildiginde fusion modeli saldiri turunu neredeyse dogrudan devralir. Bu feature cikarildiginda attack type performansi belirgin sekilde duser.

Dolayisiyla fusion katmaninin risk karari anlamli gorunse de, attack type tahmini icin `all` sonucu tek basina guclu bir kanit degildir. Raporlamada `no_attack_type` ve `visual_only` ablation sonuclari mutlaka belirtilmelidir.

## 7. Nihai Teknik Degerlendirme

### Guclu Noktalar

- CIC binary saldiri tespiti cok guclu.
- CARLA strict attack type modeli leakage azaltildiktan sonra bile makul performans veriyor.
- Fusion risk karari ablation testlerinde de yuksek kaliyor.
- nuScenes katmani gorsel tutarlilik icin kullanilabilir feature'lar uretiyor.
- Raporlama sistemi accuracy, F1, log loss ve confusion matrix cikariyor.

### Riskli Noktalar

- CARLA baseline skorlarinda leakage etkisi var.
- Fusion attack type skoru `carla_attack_type` feature'ina fazla bagimli.
- nuScenes gorsel katmani tek basina attack type ayrimi icin yeterli degil.
- CIC attack type modeli belirli siniflarda karisiklik yasiyor.

### Raporlarda Kullanilmasi Gereken Denge

Yaniltici ifade:

> Sistem tum katmanlarda %99-%100 basari verdi.

Daha dogru ifade:

> Baseline deneylerde CARLA ve fusion katmanlari cok yuksek skorlar uretmistir; ancak leakage ve ablation analizleri bu skorlarin iyimser oldugunu gostermistir. Strict/no-leakage CARLA deneyinde binary performans dusmus, attack type performansi daha gercekci bir seviyeye inmistir. Fusion attack type performansi ise `carla_attack_type` feature'ina guclu bagimlilik gostermistir. Bu nedenle nihai degerlendirme strict feature setleri ve ablation sonuclariyla birlikte raporlanmalidir.

## 8. Onerilen Nihai Deney Komutlari

Daha gercekci CARLA modeli:

```bash
python -m src.security_pipeline.cli train-carla \
  --output models/carla_strict_v2 \
  --strict-features \
  --n-estimators 500 \
  --verbose 1
```

Daha durust fusion modeli:

```bash
python -m src.security_pipeline.cli train-fusion \
  --carla-model models/carla_strict_v2 \
  --output models/fusion_no_attack_type_v2 \
  --feature-set no_attack_type \
  --max-rows 20000 \
  --visual-samples 20000 \
  --n-estimators 600 \
  --verbose 1
```

Fusion test metrikleri:

```bash
python -m src.security_pipeline.cli eval-fusion \
  --carla-model models/carla_strict_v2 \
  --fusion-model models/fusion_no_attack_type_v2 \
  --max-rows 3000 \
  --visual-samples 10000 \
  --metrics-dir reports/fusion_no_attack_type_v2_metrics \
  --output reports/fusion_no_attack_type_v2_metrics.json
```

## 9. Rapor Dosyalari

Bu raporun dayandigi dosyalar:

- `reports/training_results_summary.md`
- `reports/training_results_summary.json`
- `reports/leakage_test_smoke.md`
- `reports/leakage_test_smoke.json`

Confusion matrix dosyalari:

- `models/cic_v2/metrics/cic_validation_binary_confusion_matrix.csv`
- `models/cic_v2/metrics/cic_validation_attack_type_confusion_matrix.csv`
- `models/carla_v2/metrics/carla_validation_binary_confusion_matrix.csv`
- `models/carla_v2/metrics/carla_validation_attack_type_confusion_matrix.csv`
- `models/fusion_v2/metrics/fusion_validation_risk_confusion_matrix.csv`
- `models/fusion_v2/metrics/fusion_validation_attack_type_confusion_matrix.csv`
- `models/leakage_test_smoke/*/metrics/*_confusion_matrix.csv`

## 10. Sonuc

Calisma basarili bir prototip mimari ortaya koymustur; ancak ilk yuksek skorlar tek basina nihai basari kaniti degildir. Leakage testi, CARLA ve fusion sonuclarinin bir kisminin kolaylastirici feature'lardan kaynaklandigini gostermistir. En saglam raporlama sekli, baseline sonuclari strict/no-leakage ve ablation sonuclariyla birlikte vermektir.

Kisa nihai sonuc:

```text
CIC binary: guclu
CIC attack type: iyilestirilmeli
CARLA baseline: cok yuksek ama leakage riski var
CARLA strict: daha gercekci
Fusion risk: guclu
Fusion attack type: carla_attack_type'a bagimli
nuScenes: karar destek/gorsel tutarlilik katmani olarak anlamli
```

## 11. Final Strict Deney Sonuclari

Bu bolum, daha sonra calistirilan daha gercekci final strict deneylerin sonuclarini ekler.

Kullanilan modeller:

- `models/carla_strict_final`
- `models/fusion_no_attack_type_final`

Degerlendirme raporlari:

- `reports/final_strict_metrics.json`
- `reports/final_strict_metrics/fusion_test_risk_metrics.json`
- `reports/final_strict_metrics/fusion_test_attack_type_metrics.json`

### 11.1 CARLA Strict Final

CARLA strict final modelinde leakage riski yuksek feature'lar cikarilmistir.

| Model | Accuracy | Macro F1 | Weighted F1 | Log Loss |
|---|---:|---:|---:|---:|
| CARLA strict final binary | 0.7960 | 0.7960 | 0.7960 | 0.4106 |
| CARLA strict final attack type | 0.6881 | 0.6843 | 0.6843 | 1.0596 |

Confusion matrix ozeti:

```text
Binary:
true normal -> predicted normal: 3302
true normal -> predicted attack: 748
true attack -> predicted normal: 904
true attack -> predicted attack: 3146
```

Yorum:

```text
Strict CARLA binary performansi onceki smoke strict testine gore daha iyi:
0.5838 -> 0.7960
```

Bu, daha uzun egitim ve daha fazla agacla strict feature setinin anlamli sinyal tasidigini gosterir. Ancak baseline'daki 1.0000 sonucuna gore daha gercekci ve savunulabilir bir seviyededir.

Attack type tarafinda performans:

```text
accuracy: 0.6881
macro F1: 0.6843
```

Bu sonuc, leakage cikarildiginda saldiri turu ayriminin zorlastigini gosterir. En cok karisan siniflar sunlardir:

- `delayed_sensor_attack`
- `dos`
- `heading_spoofing`
- `sudden_brake`
- `position_spoofing`
- `gps_spoofing`

### 11.2 Fusion No-Attack-Type Final Validation

Fusion final modeli `feature-set no_attack_type` ile egitilmistir. Yani fusion modeline `carla_attack_type` dogrudan verilmemistir.

Validation sonucu:

| Model | Accuracy | Macro F1 | Weighted F1 | Log Loss |
|---|---:|---:|---:|---:|
| Fusion no_attack_type validation risk | 1.0000 | 1.0000 | 1.0000 | 0.0009 |
| Fusion no_attack_type validation attack type | 0.6605 | 0.4954 | 0.6468 | 0.8183 |

Yorum:

Risk validation sonucu yine cok yuksek gorunmektedir. Ancak attack type validation sonucu daha gercekci bir seviyeye inmistir:

```text
type accuracy: 0.6605
macro F1: 0.4954
```

Bu, `carla_attack_type` cikarildiginda fusion attack type tahmininin ciddi sekilde zorlastigini onceki ablation testiyle uyumlu bicimde dogrular.

### 11.3 Fusion No-Attack-Type Final Test

Asil dikkate alinmasi gereken sonuc, `eval-fusion` ile uretilen test sonucudur:

| Model | Accuracy | Macro F1 | Weighted F1 | Log Loss |
|---|---:|---:|---:|---:|
| Fusion no_attack_type test risk | 0.8028 | 0.7452 | 0.8203 | 1.5344 |
| Fusion no_attack_type test attack type | 0.3970 | 0.3317 | 0.3609 | 4.5511 |

Fusion test confusion matrix ozeti:

```text
Risk:
true attack -> predicted attack: 3196
true attack -> predicted normal: 854
true normal -> predicted attack: 132
true normal -> predicted normal: 818
```

Bu tabloya gore:

```text
attack recall = 3196 / (3196 + 854) ≈ 0.789
normal recall = 818 / (818 + 132) ≈ 0.861
```

Yorum:

- Fusion risk modeli test setinde kullanilabilir ama kusursuz degildir.
- Validation risk 1.0000 iken test risk 0.8028'e dusmustur.
- Bu, validation skorunun iyimser oldugunu ve gercek degerlendirmenin test seti uzerinden yapilmasi gerektigini gosterir.

Attack type test sonucu zayiftir:

```text
accuracy: 0.3970
macro F1: 0.3317
log loss: 4.5511
```

Bu, final fusion katmaninin `carla_attack_type` olmadan saldiri turunu guvenilir sekilde ayirmadigini gosterir. Bu durumda en dogru mimari yorumu sudur:

> Fusion katmani risk karari icin kullanilmali; attack type karari ise esas olarak CARLA/CIC multiclass modellerinden gelmeli veya ayrica daha guclu bir final type modeli tasarlanmalidir.

### 11.4 Final Strict Sonuclardan Cikarim

Final strict deneyler onceki yorumu guclendirdi:

1. Baseline CARLA/Fusion sonuclari fazla iyimserdi.
2. Strict CARLA daha gercekci performans verdi.
3. Fusion risk modeli anlamli ama testte kusursuz degil.
4. Fusion attack type modeli, `carla_attack_type` olmadan zayif kaliyor.
5. nuScenes gorsel katmani tek basina type tespiti icin yeterli degil; daha cok tutarlilik ve risk destek katmani olarak konumlanmali.

Guncel en dogru raporlama:

```text
CARLA strict final binary: 0.7960 accuracy
CARLA strict final attack type: 0.6881 accuracy
Fusion no_attack_type final risk test: 0.8028 accuracy
Fusion no_attack_type final attack type test: 0.3970 accuracy
```

Bu nedenle nihai tez/rapor dilinde su ifade kullanilmalidir:

> Full-feature deneylerde cok yuksek skorlar elde edilmis, ancak leakage analizi bu skorlarin iyimser oldugunu gostermistir. Strict/no-leakage ve no-attack-type fusion deneylerinde performans daha gercekci seviyelere inmistir. Final karar katmani risk tespiti icin anlamli performans sunarken, saldiri turu tahmini halen gelistirilmeye aciktir.
