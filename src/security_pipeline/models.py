from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .data import normalize_binary_labels


DROP_COLUMNS = {
    "timestamp",
    "frame",
    "scenario_id",
    "run_id",
    "attack_run_id",
    "class_run_id",
    "tick_in_run",
    "vehicle_id",
}

LEAKAGE_PRONE_COLUMNS = {
    "attack_type",
    "multiclass_label",
    "binary_label",
    "normal_subtype",
    "gps_spoof_subtype",
    "delayed_sensor_flag",
    "heading_spoof_flag",
    "hard_brake_flag",
    "position_jump_flag",
    "stale_packet_flag",
    "speed_spoof_ratio",
    "speed_spoof_offset",
    "packet_delay_steps",
    "sensor_delay_steps",
    "gps_drift_magnitude",
    "gps_drift_rate",
    "position_jump_magnitude",
    "missing_ratio",
}


@dataclass
class HierarchicalPrediction:
    attack_probability: float
    is_attack: bool
    attack_type: str
    attack_type_confidence: float


def _feature_columns(
    df: pd.DataFrame,
    labels: set[str],
    strict_features: bool = False,
) -> list[str]:
    excluded = labels | DROP_COLUMNS
    if strict_features:
        excluded = excluded | LEAKAGE_PRONE_COLUMNS
    return [c for c in df.columns if c not in excluded]


def _build_preprocessor(df: pd.DataFrame, feature_cols: list[str]) -> ColumnTransformer:
    numeric_cols = [c for c in feature_cols if pd.api.types.is_numeric_dtype(df[c])]
    categorical_cols = [c for c in feature_cols if c not in numeric_cols]
    numeric = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=5)),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric, numeric_cols),
            ("cat", categorical, categorical_cols),
        ],
        remainder="drop",
    )


def _build_classifier(
    random_state: int,
    n_estimators: int,
    verbose: int = 0,
) -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=n_estimators,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        n_jobs=-1,
        random_state=random_state,
        verbose=verbose,
    )


class HierarchicalTabularModel:
    def __init__(
        self,
        binary_model: Pipeline,
        multiclass_model: Pipeline,
        feature_cols: list[str],
        binary_label: str,
        multiclass_label: str,
    ) -> None:
        self.binary_model = binary_model
        self.multiclass_model = multiclass_model
        self.feature_cols = feature_cols
        self.binary_label = binary_label
        self.multiclass_label = multiclass_label

    def predict_one(self, row: pd.Series, threshold: float | None = None) -> HierarchicalPrediction:
        X = pd.DataFrame([row[self.feature_cols].to_dict()])
        attack_probability = _positive_probability(self.binary_model, X)
        is_attack = bool(self.binary_model.predict(X)[0]) if threshold is None else attack_probability >= threshold
        attack_type = "normal"
        attack_type_confidence = 1.0 - attack_probability
        if is_attack:
            probs = self.multiclass_model.predict_proba(X)[0]
            classes = self.multiclass_model.named_steps["clf"].classes_
            best_idx = int(np.argmax(probs))
            attack_type = str(classes[best_idx])
            attack_type_confidence = float(probs[best_idx])
        return HierarchicalPrediction(
            attack_probability=float(attack_probability),
            is_attack=bool(is_attack),
            attack_type=attack_type,
            attack_type_confidence=float(attack_type_confidence),
        )

    def save(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, output_dir / "hierarchical_model.joblib")

    @staticmethod
    def load(model_dir: Path) -> "HierarchicalTabularModel":
        return joblib.load(model_dir / "hierarchical_model.joblib")


def _positive_probability(model: Pipeline, X: pd.DataFrame) -> float:
    probs = model.predict_proba(X)[0]
    classes = list(model.named_steps["clf"].classes_)
    if 1 in classes:
        return float(probs[classes.index(1)])
    return float(probs[-1])


def train_hierarchical_model(
    train_df: pd.DataFrame,
    binary_label: str,
    multiclass_label: str,
    random_state: int = 42,
    n_estimators: int = 120,
    verbose: int = 0,
    strict_features: bool = False,
) -> HierarchicalTabularModel:
    labels = {binary_label, multiclass_label}
    feature_cols = _feature_columns(train_df, labels, strict_features=strict_features)
    print(f"[stage] selected_features={len(feature_cols)} strict_features={strict_features}", flush=True)
    X = train_df[feature_cols]
    y_binary = normalize_binary_labels(train_df[binary_label])
    attack_mask = y_binary == 1
    if attack_mask.sum() == 0:
        raise ValueError("Multiclass model icin saldiri ornegi bulunamadi.")

    preprocessor = _build_preprocessor(train_df, feature_cols)
    binary_model = Pipeline(
        steps=[
            (
                "prep",
                preprocessor,
            ),
            ("clf", _build_classifier(random_state, n_estimators, verbose)),
        ]
    )
    print(f"[train] binary model basliyor: rows={len(train_df)}, trees={n_estimators}", flush=True)
    binary_model.fit(X, y_binary)
    print("[train] binary model tamamlandi", flush=True)

    attack_df = train_df.loc[attack_mask]
    multiclass_preprocessor = _build_preprocessor(attack_df, feature_cols)
    multiclass_model = Pipeline(
        steps=[
            ("prep", multiclass_preprocessor),
            ("clf", _build_classifier(random_state + 1, n_estimators, verbose)),
        ]
    )
    print(
        f"[train] multiclass model basliyor: rows={len(attack_df)}, trees={n_estimators}",
        flush=True,
    )
    multiclass_model.fit(attack_df[feature_cols], attack_df[multiclass_label].astype(str))
    print("[train] multiclass model tamamlandi", flush=True)

    return HierarchicalTabularModel(
        binary_model=binary_model,
        multiclass_model=multiclass_model,
        feature_cols=feature_cols,
        binary_label=binary_label,
        multiclass_label=multiclass_label,
    )


def evaluate_model(model: HierarchicalTabularModel, df: pd.DataFrame) -> dict[str, Any]:
    X = df[model.feature_cols]
    y_binary = normalize_binary_labels(df[model.binary_label])
    binary_pred = model.binary_model.predict(X)
    result: dict[str, Any] = {
        "binary": classification_report(y_binary, binary_pred, output_dict=True, zero_division=0)
    }

    attack_mask = y_binary == 1
    if attack_mask.any():
        y_multi = df.loc[attack_mask, model.multiclass_label].astype(str)
        multi_pred = model.multiclass_model.predict(df.loc[attack_mask, model.feature_cols])
        result["multiclass"] = classification_report(
            y_multi, multi_pred, output_dict=True, zero_division=0
        )
    return result
