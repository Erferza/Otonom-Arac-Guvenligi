from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import DecisionThresholds
from .models import HierarchicalPrediction
from .visual import VisualConsistency


@dataclass(frozen=True)
class FusedDecision:
    risk_score: float
    risk_level: str
    final_attack_type: str
    safe_mode: str
    safe_mode_confidence: float
    needs_human_review: bool
    reason: str


NUMERIC_FUSION_FEATURES = [
    "cic_attack_probability",
    "cic_attack_confidence",
    "carla_attack_probability",
    "carla_attack_confidence",
    "visual_hallucination_probability",
    "visual_close_object_count",
    "visual_close_vehicle_count",
    "visual_close_vulnerable_count",
    "visual_nearest_object_m",
    "visual_has_close_hazard",
    "cic_threshold_triggered",
    "carla_threshold_triggered",
    "visual_threshold_triggered",
    "threshold_trigger_count",
    "max_layer_threshold_score",
    "cic_attack_severity",
    "carla_attack_severity",
    "max_attack_severity",
    "high_impact_attack_detected",
]

CATEGORICAL_FUSION_FEATURES = [
    "cic_attack_type",
    "carla_attack_type",
]

FUSION_FEATURES = NUMERIC_FUSION_FEATURES + CATEGORICAL_FUSION_FEATURES
FUSION_FEATURE_GROUPS = {
    "all": FUSION_FEATURES,
    "no_attack_type": [
        feature
        for feature in FUSION_FEATURES
        if feature not in {"cic_attack_type", "carla_attack_type"}
    ],
    "visual_only": [
        "visual_hallucination_probability",
        "visual_close_object_count",
        "visual_close_vehicle_count",
        "visual_close_vulnerable_count",
        "visual_nearest_object_m",
        "visual_has_close_hazard",
    ],
    "prediction_only": [
        "cic_attack_probability",
        "cic_attack_confidence",
        "cic_attack_type",
        "carla_attack_probability",
        "carla_attack_confidence",
        "carla_attack_type",
    ],
}

EMERGENCY_SAFE_MODE_ATTACKS = {
    "lane_deviation",
    "position_spoofing",
    "sudden_brake",
}

DEGRADED_SAFE_MODE_ATTACKS = {
    "delayed_sensor_attack",
    "dos",
    "gps_spoofing",
    "heading_spoofing",
    "speed_spoofing",
}

ATTACK_SEVERITY = {
    "normal": 0.0,
    "none": 0.0,
    "sensor_noise": 0.35,
    "delayed_sensor_attack": 0.65,
    "dos": 0.70,
    "gps_spoofing": 0.75,
    "heading_spoofing": 0.75,
    "speed_spoofing": 0.75,
    "position_spoofing": 0.90,
    "lane_deviation": 0.95,
    "sudden_brake": 1.00,
}


class DecisionFusionModel:
    def __init__(
        self,
        risk_model: Pipeline,
        safe_mode_model: Pipeline | None = None,
        feature_names: list[str] | None = None,
        attack_type_model: Pipeline | None = None,
    ) -> None:
        self.risk_model = risk_model
        self.safe_mode_model = safe_mode_model
        self.attack_type_model = attack_type_model
        self.feature_names = feature_names or FUSION_FEATURES

    def predict(
        self,
        carla: HierarchicalPrediction,
        visual: VisualConsistency,
        cic: HierarchicalPrediction | None = None,
    ) -> FusedDecision:
        X = pd.DataFrame([fusion_feature_row(cic=cic, carla=carla, visual=visual)])
        X = X[self.feature_names]

        risk_probs = self.risk_model.predict_proba(X)[0]
        risk_classes = list(self.risk_model.named_steps["clf"].classes_)
        risk_idx = int(np.argmax(risk_probs))
        risk_level = str(risk_classes[risk_idx])
        attack_probability = _class_probability(risk_classes, risk_probs, "attack")

        safe_model = getattr(self, "safe_mode_model", None)
        if safe_model is not None:
            mode_probs = safe_model.predict_proba(X)[0]
            mode_classes = list(safe_model.named_steps["clf"].classes_)
            mode_idx = int(np.argmax(mode_probs))
            safe_mode = str(mode_classes[mode_idx])
            safe_mode_confidence = float(mode_probs[mode_idx])
            raw_safe_mode = safe_mode
            safe_mode, safe_mode_confidence, policy_reason = _apply_safe_mode_policy(
                safe_mode=safe_mode,
                safe_mode_confidence=safe_mode_confidence,
                mode_classes=mode_classes,
                mode_probs=mode_probs,
                attack_probability=attack_probability,
                carla=carla,
                visual=visual,
                cic=cic,
            )
            secondary_reason = (
                f"raw_safe_mode={raw_safe_mode}, "
                f"safe_mode_confidence={safe_mode_confidence:.3f}, "
                f"policy={policy_reason}"
            )
        else:
            safe_mode = _safe_mode_from_risk(attack_probability)
            safe_mode_confidence = float(attack_probability)
            secondary_reason = "legacy_model_safe_mode_from_risk"

        final_attack_type = _dominant_attack_type(cic=cic, carla=carla, risk_level=risk_level)

        return FusedDecision(
            risk_score=float(attack_probability),
            risk_level=risk_level,
            final_attack_type=final_attack_type,
            safe_mode=safe_mode,
            safe_mode_confidence=safe_mode_confidence,
            needs_human_review=bool(risk_level == "attack"),
            reason=(
                "ml_decision "
                f"attack_probability={attack_probability:.3f}, "
                f"{secondary_reason}"
            ),
        )

    def save(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, output_dir / "decision_fusion_model.joblib")

    @staticmethod
    def load(model_dir: Path) -> "DecisionFusionModel":
        return joblib.load(model_dir / "decision_fusion_model.joblib")


def fusion_feature_row(
    carla: HierarchicalPrediction,
    visual: VisualConsistency,
    cic: HierarchicalPrediction | None = None,
) -> dict[str, float | str]:
    context = visual.context
    thresholds = DecisionThresholds()
    cic_score = float(cic.attack_probability if cic else 0.0)
    carla_score = float(carla.attack_probability)
    visual_score = float(visual.hallucination_probability)
    cic_attack_type = str(cic.attack_type if cic else "none")
    carla_attack_type = str(carla.attack_type)
    cic_severity = _attack_severity(cic_attack_type) if cic_score >= thresholds.binary_attack else 0.0
    carla_severity = _attack_severity(carla_attack_type) if carla_score >= thresholds.binary_attack else 0.0
    cic_triggered = float(cic_score >= thresholds.binary_attack) if cic else 0.0
    carla_triggered = float(carla_score >= thresholds.binary_attack)
    visual_triggered = float(visual_score >= thresholds.visual_hallucination)
    return {
        "cic_attack_probability": cic_score,
        "cic_attack_confidence": float(cic.attack_type_confidence if cic else 0.0),
        "cic_attack_type": cic_attack_type,
        "carla_attack_probability": carla_score,
        "carla_attack_confidence": float(carla.attack_type_confidence),
        "carla_attack_type": carla_attack_type,
        "visual_hallucination_probability": visual_score,
        "visual_close_object_count": float(context.close_object_count),
        "visual_close_vehicle_count": float(context.close_vehicle_count),
        "visual_close_vulnerable_count": float(context.close_vulnerable_count),
        "visual_nearest_object_m": float(
            context.nearest_object_m if context.nearest_object_m is not None else 999.0
        ),
        "visual_has_close_hazard": float(context.has_close_hazard),
        "cic_threshold_triggered": cic_triggered,
        "carla_threshold_triggered": carla_triggered,
        "visual_threshold_triggered": visual_triggered,
        "threshold_trigger_count": cic_triggered + carla_triggered + visual_triggered,
        "max_layer_threshold_score": max(cic_score, carla_score, visual_score),
        "cic_attack_severity": cic_severity,
        "carla_attack_severity": carla_severity,
        "max_attack_severity": max(cic_severity, carla_severity),
        "high_impact_attack_detected": float(max(cic_severity, carla_severity) >= 0.90),
    }


def train_decision_fusion_model(
    feature_rows: list[dict[str, float | str]],
    risk_labels: list[str],
    safe_mode_labels: list[str],
    random_state: int = 42,
    n_estimators: int = 160,
    verbose: int = 0,
    feature_set: str = "all",
) -> DecisionFusionModel:
    feature_names = FUSION_FEATURE_GROUPS[feature_set]
    X = pd.DataFrame(feature_rows)[feature_names]
    risk_model = _classifier(random_state, n_estimators, verbose, feature_names)
    safe_mode_model = _classifier(random_state + 1, n_estimators, verbose, feature_names)
    print(f"[train] fusion risk model basliyor: rows={len(X)}, trees={n_estimators}", flush=True)
    risk_model.fit(X, pd.Series(risk_labels).astype(str))
    print("[train] fusion risk model tamamlandi", flush=True)
    print(
        f"[train] fusion safe-mode model basliyor: rows={len(X)}, trees={n_estimators}",
        flush=True,
    )
    safe_mode_model.fit(X, pd.Series(safe_mode_labels).astype(str))
    print("[train] fusion safe-mode model tamamlandi", flush=True)
    return DecisionFusionModel(
        risk_model=risk_model,
        safe_mode_model=safe_mode_model,
        feature_names=feature_names,
    )


def _classifier(
    random_state: int,
    n_estimators: int,
    verbose: int = 0,
    feature_names: list[str] | None = None,
) -> Pipeline:
    feature_names = feature_names or FUSION_FEATURES
    numeric_features = [f for f in NUMERIC_FUSION_FEATURES if f in feature_names]
    categorical_features = [f for f in CATEGORICAL_FUSION_FEATURES if f in feature_names]
    transformers = []
    if numeric_features:
        transformers.append(
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_features,
            )
        )
    if categorical_features:
        transformers.append(
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_features,
            )
        )
    preprocessor = ColumnTransformer(
        transformers=transformers
    )
    return Pipeline(
        steps=[
            ("prep", preprocessor),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=n_estimators,
                    min_samples_leaf=2,
                    class_weight="balanced_subsample",
                    n_jobs=-1,
                    random_state=random_state,
                    verbose=verbose,
                ),
            ),
        ]
    )


def _class_probability(classes: list[object], probs: np.ndarray, class_name: str) -> float:
    class_values = [str(c) for c in classes]
    if class_name in class_values:
        return float(probs[class_values.index(class_name)])
    return float(np.max(probs))


def _attack_severity(attack_type: str) -> float:
    return ATTACK_SEVERITY.get(str(attack_type), 0.50)


def _dominant_attack_type(
    carla: HierarchicalPrediction,
    risk_level: str,
    cic: HierarchicalPrediction | None = None,
) -> str:
    if risk_level == "normal":
        return "normal"
    if carla.is_attack:
        return carla.attack_type
    if cic is not None and cic.is_attack:
        return cic.attack_type
    return "unknown"


def _apply_safe_mode_policy(
    safe_mode: str,
    safe_mode_confidence: float,
    mode_classes: list[object],
    mode_probs: np.ndarray,
    attack_probability: float,
    carla: HierarchicalPrediction,
    visual: VisualConsistency,
    cic: HierarchicalPrediction | None = None,
) -> tuple[str, float, str]:
    thresholds = DecisionThresholds()
    carla_attack_type = str(carla.attack_type)
    cic_attack_type = str(cic.attack_type) if cic is not None else "none"
    visual_score = float(visual.hallucination_probability)
    max_layer_score = max(
        float(attack_probability),
        float(carla.attack_probability),
        float(cic.attack_probability if cic is not None else 0.0),
        visual_score,
    )

    if (
        attack_probability < thresholds.binary_attack
        and float(carla.attack_probability) < thresholds.binary_attack
        and (cic is None or float(cic.attack_probability) < thresholds.binary_attack)
        and visual_score < thresholds.visual_hallucination
    ):
        return "normal_mode", _mode_probability(mode_classes, mode_probs, "normal_mode"), "all_layers_below_threshold"

    if (
        max_layer_score >= thresholds.critical_risk
        and (
            carla_attack_type in EMERGENCY_SAFE_MODE_ATTACKS
            or cic_attack_type in EMERGENCY_SAFE_MODE_ATTACKS
            or visual_score >= thresholds.critical_risk
        )
    ):
        return "emergency_safe_mode", _mode_probability(mode_classes, mode_probs, "emergency_safe_mode"), "critical_high_impact_signal"

    if safe_mode == "normal_mode" and attack_probability >= thresholds.high_risk:
        fallback = _best_allowed_mode(
            mode_classes,
            mode_probs,
            allowed=("emergency_safe_mode", "degraded_safe_mode", "monitoring_mode"),
            default="degraded_safe_mode",
        )
        return fallback, _mode_probability(mode_classes, mode_probs, fallback), "normal_blocked_by_high_risk"

    if safe_mode == "normal_mode" and attack_probability >= thresholds.binary_attack:
        return "monitoring_mode", _mode_probability(mode_classes, mode_probs, "monitoring_mode"), "normal_blocked_by_attack_risk"

    return safe_mode, safe_mode_confidence, "model_safe_mode_accepted"


def _best_allowed_mode(
    mode_classes: list[object],
    mode_probs: np.ndarray,
    allowed: tuple[str, ...],
    default: str,
) -> str:
    class_values = [str(c) for c in mode_classes]
    candidates = [(mode, float(mode_probs[class_values.index(mode)])) for mode in allowed if mode in class_values]
    if not candidates:
        return default
    return max(candidates, key=lambda item: item[1])[0]


def _mode_probability(mode_classes: list[object], mode_probs: np.ndarray, mode: str) -> float:
    class_values = [str(c) for c in mode_classes]
    if mode in class_values:
        return float(mode_probs[class_values.index(mode)])
    return 0.0


def _safe_mode_from_risk(risk_score: float) -> str:
    thresholds = DecisionThresholds()
    if risk_score >= thresholds.critical_risk:
        return "emergency_safe_mode"
    if risk_score >= thresholds.high_risk:
        return "degraded_safe_mode"
    if risk_score >= thresholds.binary_attack:
        return "monitoring_mode"
    return "normal_mode"
