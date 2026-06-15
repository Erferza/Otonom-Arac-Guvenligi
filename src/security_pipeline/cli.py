from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from .config import DatasetPaths
from .data import (
    balanced_sample,
    infer_binary_label,
    infer_multiclass_label,
    normalize_binary_labels,
    read_table,
)
from .fusion import (
    DEGRADED_SAFE_MODE_ATTACKS,
    EMERGENCY_SAFE_MODE_ATTACKS,
    FUSION_FEATURE_GROUPS,
    DecisionFusionModel,
    fusion_feature_row,
    train_decision_fusion_model,
)
from .metrics import evaluate_classifier_outputs
from .models import (
    HierarchicalPrediction,
    HierarchicalTabularModel,
    evaluate_model,
    train_hierarchical_model,
)
from .ollama import interpret_report_with_ollama
from .progress import ProgressPrinter
from .report import build_report, event_to_dict, render_dashboard, render_readable_report
from .thresholds import assess_event_thresholds, threshold_decision_to_dict
from .visual import NuScenesContextIndex, assess_visual_consistency


def main() -> None:
    parser = argparse.ArgumentParser(description="Katmanli guvenlik veriseti pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("inspect", help="Veri seti yollarini ve temel semalari kontrol eder")

    train_carla = sub.add_parser("train-carla", help="CARLA tabular modelini egitir")
    train_carla.add_argument("--output", type=Path, required=True)
    train_carla.add_argument("--max-rows", type=int, default=None)
    train_carla.add_argument("--n-estimators", type=int, default=120)
    train_carla.add_argument("--verbose", type=int, default=1)
    train_carla.add_argument("--strict-features", action="store_true")

    train_cic = sub.add_parser("train-cic", help="CIC-ToN-IoT modelini egitir")
    train_cic.add_argument("--output", type=Path, required=True)
    train_cic.add_argument("--max-rows", type=int, default=None)
    train_cic.add_argument("--binary-label", default=None)
    train_cic.add_argument("--multiclass-label", default=None)
    train_cic.add_argument("--n-estimators", type=int, default=120)
    train_cic.add_argument("--verbose", type=int, default=1)

    eval_cic = sub.add_parser("eval-cic", help="CIC-ToN-IoT modelini holdout/test bolumunde degerlendirir")
    eval_cic.add_argument("--model", type=Path, required=True)
    eval_cic.add_argument("--output", type=Path, required=True)
    eval_cic.add_argument("--max-rows", type=int, default=None)
    eval_cic.add_argument("--binary-label", default=None)
    eval_cic.add_argument("--multiclass-label", default=None)
    eval_cic.add_argument("--test-size", type=float, default=0.2)
    eval_cic.add_argument("--metrics-dir", type=Path, default=None)

    eval_carla = sub.add_parser("eval-carla", help="CARLA tabular modelini test CSV uzerinde degerlendirir")
    eval_carla.add_argument("--model", type=Path, required=True)
    eval_carla.add_argument("--output", type=Path, required=True)
    eval_carla.add_argument("--max-rows", type=int, default=None)
    eval_carla.add_argument("--metrics-dir", type=Path, default=None)

    train_fusion = sub.add_parser(
        "train-fusion", help="CIC/CARLA/nuScenes feature'lariyla ML karar katmanini egitir"
    )
    train_fusion.add_argument("--carla-model", type=Path, required=True)
    train_fusion.add_argument("--cic-model", type=Path, default=None)
    train_fusion.add_argument("--output", type=Path, required=True)
    train_fusion.add_argument("--max-rows", type=int, default=5000)
    train_fusion.add_argument("--cic-max-rows", type=int, default=None)
    train_fusion.add_argument("--visual-samples", type=int, default=5000)
    train_fusion.add_argument("--n-estimators", type=int, default=160)
    train_fusion.add_argument("--verbose", type=int, default=1)
    train_fusion.add_argument(
        "--feature-set",
        choices=sorted(FUSION_FEATURE_GROUPS),
        default="all",
    )

    eval_fusion = sub.add_parser(
        "eval-fusion", help="ML karar katmanini dengeli test ornegiyle degerlendirir"
    )
    eval_fusion.add_argument("--carla-model", type=Path, required=True)
    eval_fusion.add_argument("--cic-model", type=Path, default=None)
    eval_fusion.add_argument("--fusion-model", type=Path, required=True)
    eval_fusion.add_argument("--output", type=Path, required=True)
    eval_fusion.add_argument("--max-rows", type=int, default=2000)
    eval_fusion.add_argument("--cic-max-rows", type=int, default=None)
    eval_fusion.add_argument("--visual-samples", type=int, default=5000)
    eval_fusion.add_argument("--metrics-dir", type=Path, default=None)

    demo = sub.add_parser("demo", help="CARLA + nuScenes uzerinde rapor akisini calistirir")
    demo.add_argument("--carla-model", type=Path, default=None)
    demo.add_argument("--cic-model", type=Path, default=None)
    demo.add_argument("--fusion-model", type=Path, required=True)
    demo.add_argument("--limit", type=int, default=200)
    demo.add_argument("--cic-max-rows", type=int, default=None)
    demo.add_argument("--output", type=Path, required=True)
    demo.add_argument("--visual-samples", type=int, default=500)
    demo.add_argument("--ollama-model", default=None)
    demo.add_argument("--ollama-url", default="http://localhost:11434/api/generate")
    demo.add_argument(
        "--sample-mode",
        choices=["head", "balanced", "random"],
        default="balanced",
        help="Rapor icin test setinden nasil ornek secilecegi",
    )

    render_report = sub.add_parser(
        "render-report", help="JSON demo raporunu okunabilir Markdown rapora cevirir"
    )
    render_report.add_argument("--input", type=Path, required=True)
    render_report.add_argument("--output", type=Path, default=None)

    interpret_report = sub.add_parser(
        "interpret-report", help="Mevcut JSON rapora Ollama yorumu ekler ve Markdown raporu yeniler"
    )
    interpret_report.add_argument("--input", type=Path, required=True)
    interpret_report.add_argument("--output", type=Path, default=None)
    interpret_report.add_argument("--ollama-model", required=True)
    interpret_report.add_argument("--ollama-url", default="http://localhost:11434/api/generate")

    render_dashboard_cmd = sub.add_parser(
        "render-dashboard", help="JSON demo raporundan indirilebilir HTML dashboard uretir"
    )
    render_dashboard_cmd.add_argument("--input", type=Path, required=True)
    render_dashboard_cmd.add_argument("--output", type=Path, default=None)
    render_dashboard_cmd.add_argument("--markdown", type=Path, default=None)

    leakage = sub.add_parser(
        "leakage-test",
        help="Kucuk olcekli no-leakage ve fusion ablation testi calistirir",
    )
    leakage.add_argument("--output", type=Path, default=Path("reports/leakage_test.json"))
    leakage.add_argument("--work-dir", type=Path, default=Path("models/leakage_test"))
    leakage.add_argument("--max-rows", type=int, default=3000)
    leakage.add_argument("--visual-samples", type=int, default=3000)
    leakage.add_argument("--n-estimators", type=int, default=120)
    leakage.add_argument("--verbose", type=int, default=0)

    args = parser.parse_args()
    paths = DatasetPaths()

    if args.command == "inspect":
        inspect(paths)
    elif args.command == "train-carla":
        train_carla_model(
            paths,
            args.output,
            args.max_rows,
            args.n_estimators,
            args.verbose,
            args.strict_features,
        )
    elif args.command == "train-cic":
        train_cic_model(
            paths,
            args.output,
            args.max_rows,
            args.binary_label,
            args.multiclass_label,
            args.n_estimators,
            args.verbose,
        )
    elif args.command == "eval-cic":
        evaluate_cic_model(
            paths,
            model_dir=args.model,
            output=args.output,
            max_rows=args.max_rows,
            binary_label=args.binary_label,
            multiclass_label=args.multiclass_label,
            test_size=args.test_size,
            metrics_dir=args.metrics_dir,
        )
    elif args.command == "eval-carla":
        evaluate_carla_model(
            paths,
            model_dir=args.model,
            output=args.output,
            max_rows=args.max_rows,
            metrics_dir=args.metrics_dir,
        )
    elif args.command == "train-fusion":
        train_fusion_model(
            paths,
            carla_model_dir=args.carla_model,
            cic_model_dir=args.cic_model,
            output=args.output,
            max_rows=args.max_rows,
            cic_max_rows=args.cic_max_rows,
            visual_samples=args.visual_samples,
            n_estimators=args.n_estimators,
            verbose=args.verbose,
            feature_set=args.feature_set,
        )
    elif args.command == "eval-fusion":
        evaluate_fusion_model(
            paths,
            carla_model_dir=args.carla_model,
            cic_model_dir=args.cic_model,
            fusion_model_dir=args.fusion_model,
            output=args.output,
            max_rows=args.max_rows,
            cic_max_rows=args.cic_max_rows,
            visual_samples=args.visual_samples,
            metrics_dir=args.metrics_dir,
        )
    elif args.command == "demo":
        run_demo(
            paths,
            args.output,
            args.limit,
            args.visual_samples,
            args.carla_model,
            args.cic_model,
            args.fusion_model,
            args.cic_max_rows,
            args.sample_mode,
            args.ollama_model,
            args.ollama_url,
        )
    elif args.command == "render-report":
        render_report_file(args.input, args.output)
    elif args.command == "interpret-report":
        interpret_report_file(args.input, args.output, args.ollama_model, args.ollama_url)
    elif args.command == "render-dashboard":
        render_dashboard_file(args.input, args.output, args.markdown)
    elif args.command == "leakage-test":
        run_leakage_test(
            paths,
            output=args.output,
            work_dir=args.work_dir,
            max_rows=args.max_rows,
            visual_samples=args.visual_samples,
            n_estimators=args.n_estimators,
            verbose=args.verbose,
        )


def inspect(paths: DatasetPaths) -> None:
    print("Datasets")
    for name, path in {
        "CIC parquet": paths.cic_parquet,
        "CARLA train": paths.carla_train,
        "CARLA val": paths.carla_val,
        "CARLA test": paths.carla_test,
        "nuScenes meta": paths.nuscenes_meta,
    }.items():
        print(f"- {name}: {path} exists={path.exists()}")

    carla = pd.read_csv(paths.carla_train, nrows=5)
    print(f"CARLA columns ({len(carla.columns)}): {list(carla.columns)}")
    print(f"CARLA binary label: {infer_binary_label(carla)}")
    print(f"CARLA multiclass label: {infer_multiclass_label(carla)}")

    scene_count = len(json.load((paths.nuscenes_meta / "scene.json").open()))
    sample_count = len(json.load((paths.nuscenes_meta / "sample.json").open()))
    print(f"nuScenes scenes={scene_count} samples={sample_count}")


def train_carla_model(
    paths: DatasetPaths,
    output: Path,
    max_rows: int | None,
    n_estimators: int,
    verbose: int,
    strict_features: bool,
) -> None:
    print("[stage] CARLA train CSV okunuyor", flush=True)
    train_df = read_table(paths.carla_train)
    train_df = balanced_sample(train_df, "attack_type", max_rows)
    print(f"[stage] CARLA train rows={len(train_df)}", flush=True)
    print("[stage] CARLA validation CSV okunuyor", flush=True)
    val_df = read_table(paths.carla_val)
    model = train_hierarchical_model(
        train_df,
        binary_label="binary_label",
        multiclass_label="attack_type",
        n_estimators=n_estimators,
        verbose=verbose,
        strict_features=strict_features,
    )
    output.mkdir(parents=True, exist_ok=True)
    model.save(output)
    metrics = evaluate_model(model, val_df)
    _write_json(output / "validation_metrics.json", metrics)
    print(f"CARLA model kaydedildi: {output}")
    _print_hierarchical_metrics(
        model=model,
        df=val_df,
        output_dir=output / "metrics",
        prefix="carla_validation",
    )


def train_cic_model(
    paths: DatasetPaths,
    output: Path,
    max_rows: int | None,
    binary_label: str | None,
    multiclass_label: str | None,
    n_estimators: int,
    verbose: int,
) -> None:
    print("[stage] CIC parquet okunuyor", flush=True)
    df = read_table(paths.cic_parquet)
    binary_label = binary_label or infer_binary_label(df)
    multiclass_label = multiclass_label or infer_multiclass_label(df)
    if binary_label is None or multiclass_label is None:
        raise SystemExit(
            "CIC etiket kolonlari otomatik bulunamadi. "
            "--binary-label ve --multiclass-label ile belirtin."
        )
    df = balanced_sample(df, multiclass_label, max_rows)
    print(f"[stage] CIC rows={len(df)}", flush=True)
    print("[stage] CIC train/validation split hazirlaniyor", flush=True)
    train_df, val_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=df[multiclass_label].astype(str),
    )
    model = train_hierarchical_model(
        train_df,
        binary_label=binary_label,
        multiclass_label=multiclass_label,
        n_estimators=n_estimators,
        verbose=verbose,
    )
    output.mkdir(parents=True, exist_ok=True)
    model.save(output)
    print(f"CIC model kaydedildi: {output}")
    print(f"Etiketler: binary={binary_label}, multiclass={multiclass_label}")
    _print_hierarchical_metrics(
        model=model,
        df=val_df,
        output_dir=output / "metrics",
        prefix="cic_validation",
    )


def evaluate_cic_model(
    paths: DatasetPaths,
    model_dir: Path,
    output: Path,
    max_rows: int | None,
    binary_label: str | None,
    multiclass_label: str | None,
    test_size: float,
    metrics_dir: Path | None = None,
) -> None:
    print("[stage] CIC modeli yukleniyor", flush=True)
    model = HierarchicalTabularModel.load(model_dir)
    print("[stage] CIC parquet okunuyor", flush=True)
    df = read_table(paths.cic_parquet)
    binary_label = binary_label or infer_binary_label(df) or model.binary_label
    multiclass_label = multiclass_label or infer_multiclass_label(df) or model.multiclass_label
    df = balanced_sample(df, multiclass_label, max_rows)
    print(f"[stage] CIC holdout/test rows source={len(df)}", flush=True)
    _, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=42,
        stratify=df[multiclass_label].astype(str),
    )
    print(f"[stage] CIC test rows={len(test_df)}", flush=True)
    metrics = _print_hierarchical_metrics(
        model=model,
        df=test_df,
        output_dir=metrics_dir or output.parent / "cic_test_metrics",
        prefix="cic_test",
    )
    metrics["sample_count"] = len(test_df)
    _write_json(output, metrics)
    print(f"CIC test metrikleri yazildi: {output}")


def evaluate_carla_model(
    paths: DatasetPaths,
    model_dir: Path,
    output: Path,
    max_rows: int | None,
    metrics_dir: Path | None = None,
) -> None:
    print("[stage] CARLA modeli yukleniyor", flush=True)
    model = HierarchicalTabularModel.load(model_dir)
    print("[stage] CARLA test CSV okunuyor", flush=True)
    test_df = balanced_sample(read_table(paths.carla_test), "attack_type", max_rows)
    print(f"[stage] CARLA test rows={len(test_df)}", flush=True)
    metrics = _print_hierarchical_metrics(
        model=model,
        df=test_df,
        output_dir=metrics_dir or output.parent / "carla_test_metrics",
        prefix="carla_test",
    )
    metrics["sample_count"] = len(test_df)
    _write_json(output, metrics)
    print(f"CARLA test metrikleri yazildi: {output}")


def train_fusion_model(
    paths: DatasetPaths,
    carla_model_dir: Path,
    cic_model_dir: Path | None,
    output: Path,
    max_rows: int,
    cic_max_rows: int | None,
    visual_samples: int,
    n_estimators: int,
    verbose: int,
    feature_set: str,
) -> None:
    print("[stage] CARLA modeli yukleniyor", flush=True)
    carla_model = HierarchicalTabularModel.load(carla_model_dir)
    cic_model = _load_optional_model("CIC", cic_model_dir)
    print("[stage] CARLA train CSV okunuyor", flush=True)
    train_df = read_table(paths.carla_train)
    train_df = balanced_sample(train_df, "attack_type", max_rows)
    print(f"[stage] fusion rows={len(train_df)}", flush=True)
    cic_df = _load_cic_rows_for_inference(paths, cic_model, cic_max_rows or len(train_df))
    print("[stage] nuScenes gorsel indeks yukleniyor", flush=True)
    visual_index = NuScenesContextIndex(paths.nuscenes_root).load(max_samples=visual_samples)
    print(f"[stage] nuScenes sample_count={visual_index.sample_count}", flush=True)

    feature_rows = []
    decision_inputs = []
    risk_labels = []
    safe_mode_labels = []
    progress = ProgressPrinter("fusion feature extraction", len(train_df))
    for i, (_, row) in enumerate(train_df.iterrows()):
        carla_pred = carla_model.predict_one(row)
        cic_pred = _predict_paired_cic(cic_model, cic_df, i)
        context = visual_index.context_by_index(i)
        visual = assess_visual_consistency(carla_pred.attack_type, row.to_dict(), context)
        feature_rows.append(fusion_feature_row(cic=cic_pred, carla=carla_pred, visual=visual))
        decision_inputs.append((cic_pred, carla_pred, visual))

        is_attack = int(normalize_binary_labels(pd.Series([row["binary_label"]])).iloc[0]) == 1
        risk_labels.append("attack" if is_attack else "normal")
        safe_mode_labels.append(_safe_mode_label(is_attack, str(row["attack_type"]), visual))
        progress.update(i + 1)

    print("[stage] fusion train/validation split hazirlaniyor", flush=True)
    indices = list(range(len(feature_rows)))
    train_idx, val_idx = train_test_split(
        indices,
        test_size=0.2,
        random_state=42,
        stratify=safe_mode_labels,
    )
    fusion_model = train_decision_fusion_model(
        feature_rows=[feature_rows[i] for i in train_idx],
        risk_labels=[risk_labels[i] for i in train_idx],
        safe_mode_labels=[safe_mode_labels[i] for i in train_idx],
        n_estimators=n_estimators,
        verbose=verbose,
        feature_set=feature_set,
    )
    fusion_model.save(output)
    print(f"ML karar/fusion modeli kaydedildi: {output}")
    print(f"Egitim ornegi: {len(train_idx)}")
    print(f"Validation ornegi: {len(val_idx)}")
    print(f"Fusion feature_set: {feature_set}")
    safe_mode_predictions = [
        fusion_model.predict(cic=decision_inputs[i][0], carla=decision_inputs[i][1], visual=decision_inputs[i][2]).safe_mode
        for i in val_idx
    ]
    _print_fusion_metrics(
        fusion_model=fusion_model,
        feature_rows=[feature_rows[i] for i in val_idx],
        risk_labels=[risk_labels[i] for i in val_idx],
        safe_mode_labels=[safe_mode_labels[i] for i in val_idx],
        safe_mode_predictions=safe_mode_predictions,
        output_dir=output / "metrics",
        prefix="fusion_validation",
    )


def evaluate_fusion_model(
    paths: DatasetPaths,
    carla_model_dir: Path,
    cic_model_dir: Path | None,
    fusion_model_dir: Path,
    output: Path,
    max_rows: int,
    cic_max_rows: int | None,
    visual_samples: int,
    metrics_dir: Path | None = None,
) -> None:
    carla_model = HierarchicalTabularModel.load(carla_model_dir)
    cic_model = _load_optional_model("CIC", cic_model_dir)
    fusion_model = DecisionFusionModel.load(fusion_model_dir)
    test_df = balanced_sample(read_table(paths.carla_test), "attack_type", max_rows)
    print(f"[stage] fusion eval rows={len(test_df)}", flush=True)
    cic_df = _load_cic_rows_for_inference(paths, cic_model, cic_max_rows or len(test_df))
    print("[stage] nuScenes gorsel indeks yukleniyor", flush=True)
    visual_index = NuScenesContextIndex(paths.nuscenes_root).load(max_samples=visual_samples)
    print(f"[stage] nuScenes sample_count={visual_index.sample_count}", flush=True)

    feature_rows = []
    true_risk = []
    true_safe_mode = []
    safe_mode_predictions = []
    progress = ProgressPrinter("fusion eval feature extraction", len(test_df))
    for i, (_, row) in enumerate(test_df.iterrows()):
        carla_pred = carla_model.predict_one(row)
        cic_pred = _predict_paired_cic(cic_model, cic_df, i)
        context = visual_index.context_by_index(i)
        visual = assess_visual_consistency(carla_pred.attack_type, row.to_dict(), context)
        feature_rows.append(fusion_feature_row(cic=cic_pred, carla=carla_pred, visual=visual))
        safe_mode_predictions.append(fusion_model.predict(cic=cic_pred, carla=carla_pred, visual=visual).safe_mode)

        is_attack = int(normalize_binary_labels(pd.Series([row["binary_label"]])).iloc[0]) == 1
        true_risk.append("attack" if is_attack else "normal")
        true_safe_mode.append(_safe_mode_label(is_attack, str(row["attack_type"]), visual))
        progress.update(i + 1)

    metrics = _print_fusion_metrics(
        fusion_model=fusion_model,
        feature_rows=feature_rows,
        risk_labels=true_risk,
        safe_mode_labels=true_safe_mode,
        safe_mode_predictions=safe_mode_predictions,
        output_dir=metrics_dir or output.parent / "fusion_eval_metrics",
        prefix="fusion_test",
    )
    metrics["sample_count"] = len(test_df)
    _write_json(output, metrics)
    print(f"Fusion metrikleri yazildi: {output}")


def run_leakage_test(
    paths: DatasetPaths,
    output: Path,
    work_dir: Path,
    max_rows: int,
    visual_samples: int,
    n_estimators: int,
    verbose: int,
) -> None:
    os.environ.setdefault("SECURITY_PIPELINE_SKIP_PLOTS", "1")
    work_dir.mkdir(parents=True, exist_ok=True)
    print("[leakage] baseline CARLA egitiliyor", flush=True)
    baseline_dir = work_dir / "carla_baseline"
    train_carla_model(
        paths,
        output=baseline_dir,
        max_rows=max_rows,
        n_estimators=n_estimators,
        verbose=verbose,
        strict_features=False,
    )

    print("[leakage] strict/no-leakage CARLA egitiliyor", flush=True)
    strict_dir = work_dir / "carla_strict"
    train_carla_model(
        paths,
        output=strict_dir,
        max_rows=max_rows,
        n_estimators=n_estimators,
        verbose=verbose,
        strict_features=True,
    )

    fusion_results = {}
    for feature_set in ["all", "no_attack_type", "visual_only", "prediction_only"]:
        print(f"[leakage] fusion ablation egitiliyor: {feature_set}", flush=True)
        fusion_dir = work_dir / f"fusion_{feature_set}"
        train_fusion_model(
            paths,
            carla_model_dir=strict_dir,
            cic_model_dir=None,
            output=fusion_dir,
            max_rows=max_rows,
            cic_max_rows=None,
            visual_samples=visual_samples,
            n_estimators=n_estimators,
            verbose=verbose,
            feature_set=feature_set,
        )
        metrics_path = fusion_dir / "metrics" / "fusion_validation_attack_type_metrics.json"
        safe_mode_path = fusion_dir / "metrics" / "fusion_validation_safe_mode_metrics.json"
        risk_path = fusion_dir / "metrics" / "fusion_validation_risk_metrics.json"
        fusion_results[feature_set] = {
            "risk": _read_json_if_exists(risk_path),
            "safe_mode": _read_json_if_exists(safe_mode_path),
            "attack_type": _read_json_if_exists(metrics_path),
        }

    report = {
        "config": {
            "max_rows": max_rows,
            "visual_samples": visual_samples,
            "n_estimators": n_estimators,
        },
        "carla_baseline": {
            "binary": _read_json_if_exists(
                baseline_dir / "metrics" / "carla_validation_binary_metrics.json"
            ),
            "attack_type": _read_json_if_exists(
                baseline_dir / "metrics" / "carla_validation_attack_type_metrics.json"
            ),
        },
        "carla_strict": {
            "binary": _read_json_if_exists(
                strict_dir / "metrics" / "carla_validation_binary_metrics.json"
            ),
            "attack_type": _read_json_if_exists(
                strict_dir / "metrics" / "carla_validation_attack_type_metrics.json"
            ),
        },
        "fusion_ablation": fusion_results,
    }
    _write_json(output, report)
    _write_leakage_markdown(output.with_suffix(".md"), report)
    print(f"[leakage] rapor yazildi: {output}", flush=True)
    print(f"[leakage] markdown rapor yazildi: {output.with_suffix('.md')}", flush=True)


def run_demo(
    paths: DatasetPaths,
    output: Path,
    limit: int,
    visual_samples: int,
    carla_model_dir: Path | None,
    cic_model_dir: Path | None,
    fusion_model_dir: Path,
    cic_max_rows: int | None,
    sample_mode: str,
    ollama_model: str | None,
    ollama_url: str,
) -> None:
    carla_df = _select_demo_rows(read_table(paths.carla_test), limit, sample_mode)
    model = HierarchicalTabularModel.load(carla_model_dir) if carla_model_dir else None
    cic_model = _load_optional_model("CIC", cic_model_dir)
    cic_df = _load_cic_rows_for_inference(paths, cic_model, cic_max_rows or len(carla_df))
    fusion_model = DecisionFusionModel.load(fusion_model_dir)
    visual_index = NuScenesContextIndex(paths.nuscenes_root).load(max_samples=visual_samples)
    events = []
    progress = ProgressPrinter("demo event inference", len(carla_df))

    for i, (_, row) in enumerate(carla_df.iterrows()):
        carla_pred = (
            model.predict_one(row)
            if model
            else _prediction_from_labels(row)
        )
        cic_pred = _predict_paired_cic(cic_model, cic_df, i)
        context = visual_index.context_by_index(i)
        visual = assess_visual_consistency(carla_pred.attack_type, row.to_dict(), context)
        decision = fusion_model.predict(cic=cic_pred, carla=carla_pred, visual=visual)
        threshold_decision = assess_event_thresholds(
            cic=cic_pred,
            carla=carla_pred,
            visual=visual,
            fusion=decision,
        )
        events.append(
            event_to_dict(
                index=i,
                timestamp=row.get("timestamp"),
                cic_prediction=cic_pred,
                carla_prediction=carla_pred,
                visual_consistency=visual,
                decision=decision,
                threshold_decision=threshold_decision_to_dict(threshold_decision),
            )
        )
        progress.update(i + 1)

    report = build_report(events)
    if ollama_model:
        print(f"[stage] Ollama yorumlama basliyor: {ollama_model}", flush=True)
        report["llm_interpretation"] = interpret_report_with_ollama(
            report,
            model=ollama_model,
            url=ollama_url,
        )
    _write_json(output, report)
    markdown_output = output.with_suffix(".md")
    markdown_output.write_text(render_readable_report(report), encoding="utf-8")
    dashboard_output = output.with_suffix(".html")
    dashboard_output.write_text(
        render_dashboard(
            report,
            metrics=_load_safe_mode_metrics(),
            json_filename=output.name,
            markdown_filename=markdown_output.name,
        ),
        encoding="utf-8",
    )
    print(f"Rapor yazildi: {output}")
    print(f"Okunabilir rapor yazildi: {markdown_output}")
    print(f"Dashboard yazildi: {dashboard_output}")
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))


def render_report_file(input_path: Path, output_path: Path | None = None) -> None:
    report = _read_json_if_exists(input_path)
    if report is None:
        raise FileNotFoundError(f"Rapor bulunamadi: {input_path}")
    output_path = output_path or input_path.with_suffix(".md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_readable_report(report), encoding="utf-8")
    print(f"Okunabilir rapor yazildi: {output_path}")


def render_dashboard_file(
    input_path: Path,
    output_path: Path | None = None,
    markdown_path: Path | None = None,
) -> None:
    report = _read_json_if_exists(input_path)
    if report is None:
        raise FileNotFoundError(f"Rapor bulunamadi: {input_path}")
    output_path = output_path or input_path.with_suffix(".html")
    markdown_path = markdown_path or input_path.with_suffix(".md")
    metrics = _load_safe_mode_metrics()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_dashboard(
            report,
            metrics=metrics,
            json_filename=input_path.name,
            markdown_filename=markdown_path.name,
        ),
        encoding="utf-8",
    )
    print(f"Dashboard yazildi: {output_path}")


def interpret_report_file(
    input_path: Path,
    output_path: Path | None,
    ollama_model: str,
    ollama_url: str,
) -> None:
    report = _read_json_if_exists(input_path)
    if report is None:
        raise FileNotFoundError(f"Rapor bulunamadi: {input_path}")
    print(f"[stage] Ollama yorumlama basliyor: {ollama_model}", flush=True)
    report["llm_interpretation"] = interpret_report_with_ollama(
        report,
        model=ollama_model,
        url=ollama_url,
    )
    output_path = output_path or input_path
    _write_json(output_path, report)
    markdown_output = output_path.with_suffix(".md")
    markdown_output.write_text(render_readable_report(report), encoding="utf-8")
    dashboard_output = output_path.with_suffix(".html")
    dashboard_output.write_text(
        render_dashboard(
            report,
            metrics=_load_safe_mode_metrics(),
            json_filename=output_path.name,
            markdown_filename=markdown_output.name,
        ),
        encoding="utf-8",
    )
    print(f"Yorumlu JSON rapor yazildi: {output_path}")
    print(f"Okunabilir rapor yazildi: {markdown_output}")
    print(f"Dashboard yazildi: {dashboard_output}")


def _select_demo_rows(df: pd.DataFrame, limit: int, sample_mode: str) -> pd.DataFrame:
    if sample_mode == "head":
        return df.head(limit).reset_index(drop=True)
    if sample_mode == "balanced":
        return balanced_sample(df, "attack_type", limit)
    if sample_mode == "random":
        return df.sample(n=min(limit, len(df)), random_state=42).reset_index(drop=True)
    raise ValueError(f"Bilinmeyen sample mode: {sample_mode}")


def _safe_mode_label(is_attack: bool, attack_type: str, visual: object | None = None) -> str:
    if not is_attack:
        return "normal_mode"
    hallucination_probability = float(getattr(visual, "hallucination_probability", 0.0) or 0.0)
    context = getattr(visual, "context", None)
    has_close_hazard = bool(getattr(context, "has_close_hazard", False))
    if hallucination_probability >= 0.85:
        return "emergency_safe_mode"
    if hallucination_probability >= 0.70 and has_close_hazard:
        return "emergency_safe_mode"
    if attack_type in EMERGENCY_SAFE_MODE_ATTACKS:
        return "emergency_safe_mode"
    if attack_type in DEGRADED_SAFE_MODE_ATTACKS:
        return "degraded_safe_mode"
    if hallucination_probability >= 0.65:
        return "degraded_safe_mode"
    return "monitoring_mode"


def _load_optional_model(name: str, model_dir: Path | None) -> HierarchicalTabularModel | None:
    if model_dir is None:
        return None
    print(f"[stage] {name} modeli yukleniyor: {model_dir}", flush=True)
    return HierarchicalTabularModel.load(model_dir)


def _load_cic_rows_for_inference(
    paths: DatasetPaths,
    cic_model: HierarchicalTabularModel | None,
    max_rows: int | None,
) -> pd.DataFrame | None:
    if cic_model is None:
        return None
    print("[stage] CIC parquet okunuyor", flush=True)
    cic_df = read_table(paths.cic_parquet, max_rows=max_rows)
    label = cic_model.multiclass_label
    if label in cic_df.columns:
        cic_df = balanced_sample(cic_df, label, max_rows)
    elif max_rows is not None and len(cic_df) > max_rows:
        cic_df = cic_df.sample(n=max_rows, random_state=42).reset_index(drop=True)
    print(f"[stage] CIC paired rows={len(cic_df)}", flush=True)
    return cic_df.reset_index(drop=True)


def _predict_paired_cic(
    cic_model: HierarchicalTabularModel | None,
    cic_df: pd.DataFrame | None,
    index: int,
) -> HierarchicalPrediction | None:
    if cic_model is None or cic_df is None or cic_df.empty:
        return None
    row = cic_df.iloc[index % len(cic_df)]
    return cic_model.predict_one(row)


def _read_json_if_exists(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_safe_mode_metrics() -> dict[str, object]:
    result: dict[str, object] = {}
    for model_name in ("fusion_safe_mode_v1", "fusion_safe_mode_v2", "fusion_safe_mode_v3"):
        experiment_name = model_name.replace("fusion_", "", 1)
        retrain_candidates = sorted(
            Path("reports").glob(f"final_retrain_*/{model_name}_test_metrics"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        metrics_candidates = (
            *retrain_candidates,
            Path("reports") / f"{model_name}_test_metrics",
            Path("reports") / "experiments" / experiment_name / f"{model_name}_test_metrics",
        )
        metrics_dir = next((path for path in metrics_candidates if path.exists()), metrics_candidates[0])
        risk = _read_json_if_exists(metrics_dir / "fusion_test_risk_metrics.json")
        safe_mode = _read_json_if_exists(metrics_dir / "fusion_test_safe_mode_metrics.json")
        if risk or safe_mode:
            result[model_name] = {
                "risk": risk or {},
                "safe_mode": safe_mode or {},
            }
    return result


def _metric_row(metrics: dict[str, object] | None) -> str:
    if not metrics:
        return "missing | missing | missing | missing"

    def fmt(key: str) -> str:
        value = metrics.get(key)
        return "N/A" if value is None else f"{float(value):.4f}"

    return f"{fmt('accuracy')} | {fmt('macro_f1')} | {fmt('weighted_f1')} | {fmt('log_loss')}"


def _write_leakage_markdown(path: Path, report: dict[str, object]) -> None:
    lines = [
        "# Leakage Test Report",
        "",
        "## Config",
        "",
        "```json",
        json.dumps(report["config"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## CARLA Feature Leakage Check",
        "",
        "| Model | Accuracy | Macro F1 | Weighted F1 | Log Loss |",
        "|---|---:|---:|---:|---:|",
        f"| baseline binary | {_metric_row(report['carla_baseline']['binary'])} |",
        f"| baseline attack type | {_metric_row(report['carla_baseline']['attack_type'])} |",
        f"| strict binary | {_metric_row(report['carla_strict']['binary'])} |",
        f"| strict attack type | {_metric_row(report['carla_strict']['attack_type'])} |",
        "",
        "## Fusion Ablation",
        "",
        "| Feature set | Risk Accuracy | Risk Macro F1 | Safe Mode Accuracy | Safe Mode Macro F1 |",
        "|---|---:|---:|---:|---:|",
    ]
    for feature_set, metrics in report["fusion_ablation"].items():
        risk = metrics["risk"] or {}
        safe_mode = metrics.get("safe_mode") or metrics.get("attack_type") or {}
        lines.append(
            "| "
            f"{feature_set} | "
            f"{float(risk.get('accuracy', 0)):.4f} | "
            f"{float(risk.get('macro_f1', 0)):.4f} | "
            f"{float(safe_mode.get('accuracy', 0)):.4f} | "
            f"{float(safe_mode.get('macro_f1', 0)):.4f} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _print_hierarchical_metrics(
    model: HierarchicalTabularModel,
    df: pd.DataFrame,
    output_dir: Path,
    prefix: str,
) -> dict[str, object]:
    X = df[model.feature_cols]
    y_binary = normalize_binary_labels(df[model.binary_label]).astype(str)
    binary_pred = pd.Series(model.binary_model.predict(X)).astype(str)
    binary_proba = model.binary_model.predict_proba(X)
    binary_labels = [str(label) for label in model.binary_model.named_steps["clf"].classes_]
    result: dict[str, object] = {}
    result["binary"] = evaluate_classifier_outputs(
        y_true=y_binary,
        y_pred=binary_pred,
        y_proba=binary_proba,
        labels=binary_labels,
        name=f"{prefix}_binary",
        output_dir=output_dir,
    )

    attack_mask = y_binary == "1"
    if attack_mask.any():
        attack_df = df.loc[attack_mask]
        y_multi = attack_df[model.multiclass_label].astype(str)
        multi_pred = pd.Series(
            model.multiclass_model.predict(attack_df[model.feature_cols])
        ).astype(str)
        multi_proba = model.multiclass_model.predict_proba(attack_df[model.feature_cols])
        multi_labels = [str(label) for label in model.multiclass_model.named_steps["clf"].classes_]
        result["attack_type"] = evaluate_classifier_outputs(
            y_true=y_multi,
            y_pred=multi_pred,
            y_proba=multi_proba,
            labels=multi_labels,
            name=f"{prefix}_attack_type",
            output_dir=output_dir,
        )
    return result


def _print_fusion_metrics(
    fusion_model: DecisionFusionModel,
    feature_rows: list[dict[str, float | str]],
    risk_labels: list[str],
    safe_mode_labels: list[str],
    safe_mode_predictions: list[str] | None,
    output_dir: Path,
    prefix: str,
) -> dict[str, object]:
    X = pd.DataFrame(feature_rows)[fusion_model.feature_names]
    risk_pred = pd.Series(fusion_model.risk_model.predict(X)).astype(str)
    risk_proba = fusion_model.risk_model.predict_proba(X)
    risk_model_labels = [str(label) for label in fusion_model.risk_model.named_steps["clf"].classes_]
    risk_metrics = evaluate_classifier_outputs(
        y_true=risk_labels,
        y_pred=risk_pred,
        y_proba=risk_proba,
        labels=risk_model_labels,
        name=f"{prefix}_risk",
        output_dir=output_dir,
    )

    safe_model = getattr(fusion_model, "safe_mode_model", None)
    if safe_model is None:
        safe_model = getattr(fusion_model, "attack_type_model", None)
    if safe_model is None:
        return {"risk": risk_metrics}

    safe_pred = (
        pd.Series(safe_mode_predictions).astype(str)
        if safe_mode_predictions is not None
        else pd.Series(safe_model.predict(X)).astype(str)
    )
    safe_proba = safe_model.predict_proba(X)
    safe_model_labels = [str(label) for label in safe_model.named_steps["clf"].classes_]
    safe_mode_metrics = evaluate_classifier_outputs(
        y_true=safe_mode_labels,
        y_pred=safe_pred,
        y_proba=safe_proba,
        labels=safe_model_labels,
        name=f"{prefix}_safe_mode",
        output_dir=output_dir,
    )
    return {"risk": risk_metrics, "safe_mode": safe_mode_metrics}


def _prediction_from_labels(row: pd.Series) -> HierarchicalPrediction:
    binary = int(normalize_binary_labels(pd.Series([row.get("binary_label", 0)])).iloc[0])
    attack_type = str(row.get("attack_type", "normal")) if binary else "normal"
    return HierarchicalPrediction(
        attack_probability=0.92 if binary else 0.08,
        is_attack=bool(binary),
        attack_type=attack_type,
        attack_type_confidence=0.90,
    )


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
