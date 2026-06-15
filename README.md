# Guvenlik Veriseti Pipeline

Bu klasordeki uc veri kaynagi icin katmanli bir guvenlik analizi iskeleti:

1. CIC-ToN-IoT: once binary saldiri var/yok, sonra saldiri turu.
2. CARLA tabular: once binary saldiri var/yok, sonra saldiri turu.
3. nuScenes: gorsel/cevre baglami ile sensor kararini karsilastirma.
4. ML fusion/report: CIC, CARLA ve nuScenes feature'lariyla nihai karar, sure,
   siklik ve kritik bulgular.

## Kurulum

```bash
python3 -m pip install -r requirements.txt
```

Not: `CIC-ToN-IoT /CIC-ToN-IoT-V2.parquet` icin `pyarrow` gerekir.

## Hizli kontrol

```bash
python3 -m src.security_pipeline.cli inspect
python3 -m src.security_pipeline.cli demo --limit 200 --output reports/demo_report.json
```

## Model egitimi

```bash
python3 -m src.security_pipeline.cli train-carla --output models/carla --n-estimators 300 --verbose 1
python3 -m src.security_pipeline.cli train-cic --output models/cic --max-rows 200000 --n-estimators 300 --verbose 1
python3 -m src.security_pipeline.cli train-fusion --carla-model models/carla --cic-model models/cic --output models/fusion --max-rows 20000 --visual-samples 20000 --n-estimators 400 --verbose 1
```

Etiket kolonlari otomatik bulunamazsa `--binary-label` ve `--multiclass-label`
argumanlariyla verilebilir.
`--max-rows` verildiginde orneklem siniflara gore dengeli secilir.
RandomForest kullandigimiz icin klasik epoch yoktur; daha uzun egitim icin
`--n-estimators` artirilir.
`--verbose 1` terminalde model egitim ilerlemesini ve pipeline stage'lerini
yazdirir. Daha ayrintili sklearn ciktisi icin `--verbose 2` kullanilabilir.
Egitim komutlari terminale accuracy, macro F1, weighted F1, validation log loss
ve confusion matrix basar. Confusion matrix dosyalari model klasoru altindaki
`metrics/` dizinine CSV olarak yazilir; `matplotlib` kuruluysa PNG olarak da
cizilir.

Rapor uretirken final karar katmani icin egitilmis fusion modeli gerekir:

```bash
python3 -m src.security_pipeline.cli eval-fusion --carla-model models/carla --cic-model models/cic --fusion-model models/fusion --max-rows 3000 --visual-samples 10000 --output reports/fusion_metrics.json
python3 -m src.security_pipeline.cli demo --carla-model models/carla --cic-model models/cic --fusion-model models/fusion --limit 1000 --sample-mode balanced --output reports/demo.json
```
