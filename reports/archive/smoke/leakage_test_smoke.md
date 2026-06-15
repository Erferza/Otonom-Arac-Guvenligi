# Leakage Test Report

## Config

```json
{
  "max_rows": 1200,
  "visual_samples": 1200,
  "n_estimators": 80
}
```

## CARLA Feature Leakage Check

| Model | Accuracy | Macro F1 | Weighted F1 | Log Loss |
|---|---:|---:|---:|---:|
| baseline binary | 1.0000 | 1.0000 | 1.0000 | 0.0775 |
| baseline attack type | 0.9726 | 0.9726 | 0.9726 | 0.3329 |
| strict binary | 0.5838 | 0.5051 | 0.5051 | 0.7082 |
| strict attack type | 0.7314 | 0.7327 | 0.7327 | 0.9836 |

## Fusion Ablation

| Feature set | Risk Accuracy | Risk Macro F1 | Type Accuracy | Type Macro F1 |
|---|---:|---:|---:|---:|
| all | 0.9958 | 0.9882 | 0.9958 | 0.9958 |
| no_attack_type | 0.9958 | 0.9882 | 0.5042 | 0.4997 |
| visual_only | 0.9875 | 0.9632 | 0.3458 | 0.3412 |
| prediction_only | 0.9958 | 0.9882 | 0.9958 | 0.9958 |