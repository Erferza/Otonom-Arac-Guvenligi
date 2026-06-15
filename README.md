# V6 Workspace

This folder is the canonical home for the CARLA V6 dataset, training scripts, and fusion pipeline.

## Structure

```text
v6/
|-- scripts/
|   |-- 1_collect_carla_dataset_v6.py
|   |-- 2_split_by_label_v6.py
|   |-- 3_validate_carla_dataset_v6.py
|   |-- 4_train_xgboost_baseline_v6.py
|   `-- 5_train_lstm_bilstm_v6.py
|-- datasets/
|   `-- carla_tabular_dataset_v6/
|-- results/
|   |-- xgboost_v6/
|   `-- lstm_v6/
`-- security_pipeline/
    |-- pipeline/
    |   |-- risk_policy.py
    |   |-- run_cic_detector.py
    |   |-- run_carla_detector_v6.py
    |   |-- build_fusion_events_v6.py
    |   `-- fusion_pipeline_v6.py
    |-- models/
    |   |-- cic_xgboost/
    |   `-- carla_v6/
    |-- results/
    |   |-- cic/
    |   |-- carla_v6/
    |   `-- fusion_v6/
    `-- datasets/
        `-- cic/
```

## Run Order

From `PythonAPI/`:

```powershell
python "v6/scripts/1_collect_carla_dataset_v6.py"
python "v6/scripts/2_split_by_label_v6.py"
python "v6/scripts/3_validate_carla_dataset_v6.py"
python "v6/scripts/4_train_xgboost_baseline_v6.py"
python "v6/scripts/5_train_lstm_bilstm_v6.py"
python "v6/security_pipeline/pipeline/run_cic_detector.py"
python "v6/security_pipeline/pipeline/run_carla_detector_v6.py"
python "v6/security_pipeline/pipeline/build_fusion_events_v6.py"
python "v6/security_pipeline/pipeline/fusion_pipeline_v6.py"
```

## Notes

- The V6 CARLA scripts write to `v6/datasets/` and `v6/results/`.
- The V6 fusion pipeline writes to `v6/security_pipeline/results/`.
- The CIC detector first checks `v6/security_pipeline/datasets/cic/` and `v6/datasets/cic/`.
- If the large CIC parquet file is not copied into `v6/`, the V6 CIC detector can still fall back to the legacy `Guvenlik Proje/CIC-ToN-IoT-V2.parquet`.
