from __future__ import annotations

from dataclasses import dataclass, asdict

from .config import DecisionThresholds
from .fusion import FusedDecision
from .models import HierarchicalPrediction
from .visual import VisualConsistency


@dataclass(frozen=True)
class LayerThresholdResult:
    layer: str
    score: float
    level: str
    triggered: bool
    reason: str


@dataclass(frozen=True)
class ThresholdDecision:
    cic: LayerThresholdResult | None
    carla: LayerThresholdResult
    visual: LayerThresholdResult
    fusion: LayerThresholdResult
    final_level: str
    safe_mode: str
    safe_mode_required: bool
    reason: str


def assess_event_thresholds(
    carla: HierarchicalPrediction,
    visual: VisualConsistency,
    fusion: FusedDecision,
    cic: HierarchicalPrediction | None = None,
    thresholds: DecisionThresholds | None = None,
) -> ThresholdDecision:
    thresholds = thresholds or DecisionThresholds()
    cic_result = (
        _prediction_layer("cic", cic, thresholds)
        if cic is not None
        else None
    )
    carla_result = _prediction_layer("carla", carla, thresholds)
    visual_result = _visual_layer(visual, thresholds)
    fusion_result = _fusion_layer(fusion, thresholds)
    layers = [layer for layer in [cic_result, carla_result, visual_result, fusion_result] if layer]

    final_level = _max_level(layer.level for layer in layers)
    high_or_above = sum(_level_rank(layer.level) >= _level_rank("high") for layer in layers)
    critical_layers = [layer.layer for layer in layers if layer.level == "critical"]

    if critical_layers or fusion_result.level == "critical":
        safe_mode = "emergency_safe_mode"
        safe_mode_required = True
        reason = "critical_threshold_triggered: " + ",".join(critical_layers or ["fusion"])
    elif fusion_result.level == "high" or high_or_above >= 2:
        safe_mode = "degraded_safe_mode"
        safe_mode_required = True
        reason = "high_risk_consensus"
    elif final_level == "medium":
        safe_mode = "monitoring_mode"
        safe_mode_required = False
        reason = "medium_risk_monitoring"
    else:
        safe_mode = "normal_mode"
        safe_mode_required = False
        reason = "below_thresholds"

    return ThresholdDecision(
        cic=cic_result,
        carla=carla_result,
        visual=visual_result,
        fusion=fusion_result,
        final_level=final_level,
        safe_mode=safe_mode,
        safe_mode_required=safe_mode_required,
        reason=reason,
    )


def threshold_decision_to_dict(decision: ThresholdDecision) -> dict[str, object]:
    return asdict(decision)


def _prediction_layer(
    layer: str,
    prediction: HierarchicalPrediction,
    thresholds: DecisionThresholds,
) -> LayerThresholdResult:
    probability = float(prediction.attack_probability)
    confidence = float(prediction.attack_type_confidence)
    level = _score_level(probability, thresholds)
    triggered = probability >= thresholds.binary_attack
    confidence_note = (
        "low_type_confidence"
        if triggered and confidence < thresholds.multiclass_confidence
        else "type_confidence_ok"
    )
    attack_type = prediction.attack_type if triggered else "normal"
    return LayerThresholdResult(
        layer=layer,
        score=probability,
        level=level,
        triggered=triggered,
        reason=(
            f"attack_probability={probability:.3f}; "
            f"attack_type={attack_type}; "
            f"type_confidence={confidence:.3f}; "
            f"{confidence_note}"
        ),
    )


def _visual_layer(
    visual: VisualConsistency,
    thresholds: DecisionThresholds,
) -> LayerThresholdResult:
    probability = float(visual.hallucination_probability)
    level = _score_level(probability, thresholds)
    return LayerThresholdResult(
        layer="visual",
        score=probability,
        level=level,
        triggered=probability >= thresholds.visual_hallucination,
        reason=visual.explanation,
    )


def _fusion_layer(
    fusion: FusedDecision,
    thresholds: DecisionThresholds,
) -> LayerThresholdResult:
    score = float(fusion.risk_score)
    return LayerThresholdResult(
        layer="fusion",
        score=score,
        level=_score_level(score, thresholds),
        triggered=score >= thresholds.binary_attack,
        reason=fusion.reason,
    )


def _score_level(score: float, thresholds: DecisionThresholds) -> str:
    if score >= thresholds.critical_risk:
        return "critical"
    if score >= thresholds.high_risk:
        return "high"
    if score >= thresholds.binary_attack:
        return "medium"
    return "low"


def _max_level(levels: object) -> str:
    return max((str(level) for level in levels), key=_level_rank, default="low")


def _level_rank(level: str) -> int:
    return {
        "low": 0,
        "medium": 1,
        "high": 2,
        "critical": 3,
    }.get(level, 0)
