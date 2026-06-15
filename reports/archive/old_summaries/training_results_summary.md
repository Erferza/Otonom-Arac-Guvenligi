# Training Results Summary

Bu rapor `models/*/metrics` altindaki validation metriklerinden olusturuldu.

## Model Dosyalari

| Model | Boyut |
|---|---:|
| `models/carla/hierarchical_model.joblib` | 10.15 MB |
| `models/carla_smoke/hierarchical_model.joblib` | 2.6 MB |
| `models/carla_v2/hierarchical_model.joblib` | 41.16 MB |
| `models/cic/hierarchical_model.joblib` | 670.01 MB |
| `models/cic_v2/hierarchical_model.joblib` | 5596.69 MB |
| `models/fusion/decision_fusion_model.joblib` | 43.8 MB |
| `models/fusion_v2/decision_fusion_model.joblib` | 11.53 MB |

## Metrik Ozeti

| Katman | Accuracy | Macro F1 | Weighted F1 | Log Loss |
|---|---:|---:|---:|---:|
| CIC v2 binary | 0.9934 | 0.9923 | 0.9934 | 0.0261 |
| CIC v2 attack type | 0.6179 | 0.5397 | 0.6201 | 0.8173 |
| CARLA v2 binary | 1.0000 | 1.0000 | 1.0000 | 0.0059 |
| CARLA v2 attack type | 0.9765 | 0.9765 | 0.9765 | 0.2510 |
| Fusion v2 risk | 1.0000 | 1.0000 | 1.0000 | 0.0001 |
| Fusion v2 attack type | 1.0000 | 1.0000 | 1.0000 | 0.0036 |

## Confusion Matrix Dosyalari

- **CIC v2 binary**: `models/cic_v2/metrics/cic_validation_binary_confusion_matrix.csv`
- **CIC v2 attack type**: `models/cic_v2/metrics/cic_validation_attack_type_confusion_matrix.csv`
- **CARLA v2 binary**: `models/carla_v2/metrics/carla_validation_binary_confusion_matrix.csv`
- **CARLA v2 attack type**: `models/carla_v2/metrics/carla_validation_attack_type_confusion_matrix.csv`
- **Fusion v2 risk**: `models/fusion_v2/metrics/fusion_validation_risk_confusion_matrix.csv`
- **Fusion v2 attack type**: `models/fusion_v2/metrics/fusion_validation_attack_type_confusion_matrix.csv`

## Confusion Matrix Ozetleri

### CIC v2 binary

| true\pred | 0     | 1     |
| --------- | ----- | ----- |
| 0         | 30486 | 532   |
| 1         | 125   | 68857 |

### CIC v2 attack type

| true\pred  | backdoor | ddos | dos | injection | mitm | password | ransomware | scanning | xss   |
| ---------- | -------- | ---- | --- | --------- | ---- | -------- | ---------- | -------- | ----- |
| backdoor   | 5414     | 0    | 0   | 0         | 0    | 0        | 15         | 0        | 0     |
| ddos       | 0        | 2    | 19  | 0         | 19   | 0        | 0          | 0        | 0     |
| dos        | 0        | 22   | 1   | 0         | 6    | 0        | 0          | 0        | 0     |
| injection  | 0        | 2    | 0   | 4179      | 0    | 3806     | 0          | 1174     | 3061  |
| mitm       | 0        | 20   | 19  | 0         | 64   | 0        | 0          | 0        | 0     |
| password   | 0        | 0    | 0   | 2345      | 0    | 5963     | 0          | 1942     | 2578  |
| ransomware | 4        | 0    | 0   | 0         | 0    | 0        | 954        | 0        | 0     |
| scanning   | 0        | 1    | 3   | 364       | 1    | 967      | 0          | 5418     | 359   |
| xss        | 0        | 0    | 0   | 2757      | 0    | 4403     | 0          | 2474     | 20626 |

### CARLA v2 binary

| true\pred | 0    | 1    |
| --------- | ---- | ---- |
| 0         | 4050 | 0    |
| 1         | 0    | 4050 |

### CARLA v2 attack type

| true\pred             | delayed_sensor_attack | dos | gps_spoofing | heading_spoofing | lane_deviation | position_spoofing | sensor_noise | speed_spoofing | sudden_brake |
| --------------------- | --------------------- | --- | ------------ | ---------------- | -------------- | ----------------- | ------------ | -------------- | ------------ |
| delayed_sensor_attack | 415                   | 35  | 0            | 0                | 0              | 0                 | 0            | 0              | 0            |
| dos                   | 0                     | 394 | 0            | 0                | 56             | 0                 | 0            | 0              | 0            |
| gps_spoofing          | 0                     | 0   | 450          | 0                | 0              | 0                 | 0            | 0              | 0            |
| heading_spoofing      | 0                     | 0   | 0            | 450              | 0              | 0                 | 0            | 0              | 0            |
| lane_deviation        | 0                     | 0   | 0            | 0                | 450            | 0                 | 0            | 0              | 0            |
| position_spoofing     | 0                     | 0   | 0            | 0                | 0              | 450               | 0            | 0              | 0            |
| sensor_noise          | 0                     | 0   | 0            | 0                | 0              | 0                 | 450          | 0              | 0            |
| speed_spoofing        | 0                     | 0   | 0            | 0                | 0              | 0                 | 0            | 450            | 0            |
| sudden_brake          | 0                     | 4   | 0            | 0                | 0              | 0                 | 0            | 0              | 446          |

### Fusion v2 risk

| true\pred | attack | normal |
| --------- | ------ | ------ |
| attack    | 3600   | 0      |
| normal    | 0      | 400    |

### Fusion v2 attack type

| true\pred             | delayed_sensor_attack | dos | gps_spoofing | heading_spoofing | lane_deviation | normal | position_spoofing | sensor_noise | speed_spoofing | sudden_brake |
| --------------------- | --------------------- | --- | ------------ | ---------------- | -------------- | ------ | ----------------- | ------------ | -------------- | ------------ |
| delayed_sensor_attack | 400                   | 0   | 0            | 0                | 0              | 0      | 0                 | 0            | 0              | 0            |
| dos                   | 0                     | 400 | 0            | 0                | 0              | 0      | 0                 | 0            | 0              | 0            |
| gps_spoofing          | 0                     | 0   | 400          | 0                | 0              | 0      | 0                 | 0            | 0              | 0            |
| heading_spoofing      | 0                     | 0   | 0            | 400              | 0              | 0      | 0                 | 0            | 0              | 0            |
| lane_deviation        | 0                     | 0   | 0            | 0                | 400            | 0      | 0                 | 0            | 0              | 0            |
| normal                | 0                     | 0   | 0            | 0                | 0              | 400    | 0                 | 0            | 0              | 0            |
| position_spoofing     | 0                     | 0   | 0            | 0                | 0              | 0      | 400               | 0            | 0              | 0            |
| sensor_noise          | 0                     | 0   | 0            | 0                | 0              | 0      | 0                 | 400          | 0              | 0            |
| speed_spoofing        | 0                     | 0   | 0            | 0                | 0              | 0      | 0                 | 0            | 400            | 0            |
| sudden_brake          | 0                     | 0   | 0            | 0                | 0              | 0      | 0                 | 0            | 0              | 400          |

## Mevcut Demo Raporlari

- `reports/demo_report.json` (40.84 KB)

```json
{
  "event_count": 25,
  "risk_distribution": {
    "medium": 14,
    "low": 11
  },
  "review_required_count": 0,
  "top_threats": [
    {
      "attack_type": "delayed_sensor_attack",
      "count": 25
    }
  ]
}
```

- `reports/demo_with_model_report.json` (41.3 KB)

```json
{
  "event_count": 25,
  "risk_distribution": {
    "medium": 14,
    "low": 11
  },
  "review_required_count": 10,
  "top_threats": [
    {
      "attack_type": "delayed_sensor_attack",
      "count": 25
    }
  ]
}
```

- `reports/ml_fusion_demo.json` (207.91 KB)

```json
{
  "event_count": 100,
  "risk_distribution": {
    "attack": 100
  },
  "review_required_count": 100,
  "top_threats": [
    {
      "attack_type": "sudden_brake",
      "count": 86
    },
    {
      "attack_type": "dos",
      "count": 9
    },
    {
      "attack_type": "speed_spoofing",
      "count": 5
    }
  ]
}
```
