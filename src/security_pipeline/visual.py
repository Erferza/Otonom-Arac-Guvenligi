from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .data import load_json


VULNERABLE_PREFIXES = ("human.", "vehicle.bicycle", "vehicle.motorcycle")
VEHICLE_PREFIX = "vehicle."


@dataclass(frozen=True)
class VisualContext:
    sample_token: str
    scene_name: str
    timestamp: int
    close_object_count: int
    close_vehicle_count: int
    close_vulnerable_count: int
    nearest_object_m: float | None
    camera_files: list[str]

    @property
    def has_close_hazard(self) -> bool:
        return self.close_vulnerable_count > 0 or (
            self.nearest_object_m is not None and self.nearest_object_m <= 12.0
        )


@dataclass(frozen=True)
class VisualConsistency:
    hallucination_probability: float
    explanation: str
    context: VisualContext


class NuScenesContextIndex:
    def __init__(self, nuscenes_root: Path) -> None:
        self.root = nuscenes_root
        self.meta = nuscenes_root / "v1.0-trainval"
        self._scene_by_token: dict[str, dict[str, Any]] = {}
        self._samples: list[dict[str, Any]] = []
        self._ego_pose_by_token: dict[str, dict[str, Any]] = {}
        self._sample_data_by_sample: dict[str, list[dict[str, Any]]] = {}
        self._annotations_by_sample: dict[str, list[dict[str, Any]]] = {}
        self._instance_category: dict[str, str] = {}

    def load(self, max_samples: int | None = None) -> "NuScenesContextIndex":
        scenes = load_json(self.meta / "scene.json")
        self._scene_by_token = {s["token"]: s for s in scenes}
        self._samples = load_json(self.meta / "sample.json")
        if max_samples is not None:
            sample_tokens = {s["token"] for s in self._samples[:max_samples]}
            self._samples = self._samples[:max_samples]
        else:
            sample_tokens = {s["token"] for s in self._samples}

        categories = {c["token"]: c["name"] for c in load_json(self.meta / "category.json")}
        instances = load_json(self.meta / "instance.json")
        self._instance_category = {
            i["token"]: categories.get(i["category_token"], "unknown") for i in instances
        }

        for sd in load_json(self.meta / "sample_data.json"):
            token = sd["sample_token"]
            if token in sample_tokens:
                self._sample_data_by_sample.setdefault(token, []).append(sd)

        pose_tokens = {
            sd["ego_pose_token"]
            for rows in self._sample_data_by_sample.values()
            for sd in rows
            if sd.get("is_key_frame")
        }
        self._ego_pose_by_token = {
            p["token"]: p for p in load_json(self.meta / "ego_pose.json") if p["token"] in pose_tokens
        }

        for ann in load_json(self.meta / "sample_annotation.json"):
            token = ann["sample_token"]
            if token in sample_tokens:
                self._annotations_by_sample.setdefault(token, []).append(ann)
        return self

    @property
    def sample_count(self) -> int:
        return len(self._samples)

    def context_by_index(self, index: int, radius_m: float = 30.0) -> VisualContext:
        if not self._samples:
            raise RuntimeError("NuScenes index yuklenmedi.")
        sample = self._samples[index % len(self._samples)]
        return self.context_for_sample(sample["token"], radius_m=radius_m)

    def context_for_sample(self, sample_token: str, radius_m: float = 30.0) -> VisualContext:
        sample = next(s for s in self._samples if s["token"] == sample_token)
        scene = self._scene_by_token.get(sample["scene_token"], {})
        sample_data = self._sample_data_by_sample.get(sample_token, [])
        key_data = next((sd for sd in sample_data if sd.get("is_key_frame")), None)
        ego = self._ego_pose_by_token.get(key_data["ego_pose_token"]) if key_data else None
        ego_xy = tuple(ego["translation"][:2]) if ego else None

        nearest: float | None = None
        close_object_count = 0
        close_vehicle_count = 0
        close_vulnerable_count = 0
        for ann in self._annotations_by_sample.get(sample_token, []):
            distance = _distance_xy(ego_xy, ann["translation"][:2]) if ego_xy else None
            if distance is None or distance > radius_m:
                continue
            nearest = distance if nearest is None else min(nearest, distance)
            category = self._instance_category.get(ann["instance_token"], "unknown")
            close_object_count += 1
            if category.startswith(VEHICLE_PREFIX):
                close_vehicle_count += 1
            if category.startswith(VULNERABLE_PREFIXES):
                close_vulnerable_count += 1

        camera_files = [
            sd["filename"]
            for sd in sample_data
            if str(sd.get("filename", "")).startswith("samples/CAM")
        ]
        return VisualContext(
            sample_token=sample_token,
            scene_name=scene.get("name", "unknown"),
            timestamp=int(sample["timestamp"]),
            close_object_count=close_object_count,
            close_vehicle_count=close_vehicle_count,
            close_vulnerable_count=close_vulnerable_count,
            nearest_object_m=nearest,
            camera_files=camera_files,
        )


def assess_visual_consistency(
    attack_type: str,
    sensor_row: dict[str, Any],
    context: VisualContext,
) -> VisualConsistency:
    attack_type = str(attack_type)
    brake = float(sensor_row.get("brake", 0) or 0)
    hard_brake = int(sensor_row.get("hard_brake_flag", 0) or 0) == 1
    front_distance = _optional_float(sensor_row.get("front_vehicle_distance"))

    if attack_type == "sudden_brake" or hard_brake or brake >= 0.55:
        if context.has_close_hazard:
            probability = 0.18
            explanation = "Ani fren gorsel baglamla uyumlu: yakinda obje/yaya/arac var."
        elif front_distance is not None and front_distance <= 12.0:
            probability = 0.35
            explanation = "Ani fren tabular on arac mesafesiyle kismen uyumlu; gorsel destek zayif."
        else:
            probability = 0.82
            explanation = "Ani fren icin gorselde yakin tehlike yok; anomalilik olasiligi yuksek."
    elif attack_type in {"gps_spoofing", "position_spoofing", "heading_spoofing", "lane_deviation"}:
        probability = 0.60 if context.close_object_count == 0 else 0.42
        explanation = "Konum/yon saldirisi gorsel yogunluk ve cevre nesneleriyle karsilastirildi."
    elif attack_type in {"sensor_noise", "delayed_sensor_attack", "dos", "speed_spoofing"}:
        probability = 0.50
        explanation = "Gorsel katman bu saldiri turu icin destekleyici sinyal olarak kullanildi."
    else:
        probability = 0.12
        explanation = "Normal karar gorsel baglamla celismiyor."

    return VisualConsistency(
        hallucination_probability=probability,
        explanation=explanation,
        context=context,
    )


def _distance_xy(a: tuple[float, float] | None, b: list[float]) -> float | None:
    if a is None:
        return None
    return math.hypot(a[0] - float(b[0]), a[1] - float(b[1]))


def _optional_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        f = float(value)
        if math.isnan(f):
            return None
        return f
    except (TypeError, ValueError):
        return None
