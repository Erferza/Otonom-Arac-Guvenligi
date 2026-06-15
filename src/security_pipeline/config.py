from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data"


@dataclass(frozen=True)
class DatasetPaths:
    root: Path = ROOT
    data_root: Path = DATA_ROOT
    cic_parquet: Path = DATA_ROOT / "CIC-ToN-IoT " / "CIC-ToN-IoT-V2.parquet"
    carla_root: Path = DATA_ROOT / "carla_tabular_dataset_v6"
    nuscenes_root: Path = DATA_ROOT / "Nuscenes Dataset"

    @property
    def carla_train(self) -> Path:
        return self.carla_root / "train" / "train_combined.csv"

    @property
    def carla_val(self) -> Path:
        return self.carla_root / "val" / "val_combined.csv"

    @property
    def carla_test(self) -> Path:
        return self.carla_root / "test" / "test_combined.csv"

    @property
    def nuscenes_meta(self) -> Path:
        return self.nuscenes_root / "v1.0-trainval"


@dataclass(frozen=True)
class DecisionThresholds:
    binary_attack: float = 0.55
    multiclass_confidence: float = 0.45
    visual_hallucination: float = 0.65
    high_risk: float = 0.70
    critical_risk: float = 0.85
