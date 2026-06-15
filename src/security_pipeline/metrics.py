from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
)


def evaluate_classifier_outputs(
    y_true: list[str] | pd.Series,
    y_pred: list[str] | np.ndarray,
    y_proba: np.ndarray | None,
    labels: list[str],
    name: str,
    output_dir: Path,
) -> dict[str, Any]:
    y_true_s = pd.Series(y_true).astype(str)
    y_pred_s = pd.Series(y_pred).astype(str)
    labels = list(dict.fromkeys([str(label) for label in labels] + y_true_s.tolist() + y_pred_s.tolist()))
    output_dir.mkdir(parents=True, exist_ok=True)

    metrics: dict[str, Any] = {
        "accuracy": float(accuracy_score(y_true_s, y_pred_s)),
        "macro_f1": float(f1_score(y_true_s, y_pred_s, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true_s, y_pred_s, average="weighted", zero_division=0)),
        "classification_report": classification_report(
            y_true_s,
            y_pred_s,
            labels=labels,
            output_dict=True,
            zero_division=0,
        ),
    }
    if y_proba is not None:
        try:
            metrics["log_loss"] = float(log_loss(y_true_s, y_proba, labels=labels))
        except ValueError:
            metrics["log_loss"] = None

    matrix = confusion_matrix(y_true_s, y_pred_s, labels=labels)
    matrix_csv = output_dir / f"{name}_confusion_matrix.csv"
    matrix_png = output_dir / f"{name}_confusion_matrix.png"
    metrics_json = output_dir / f"{name}_metrics.json"
    pd.DataFrame(matrix, index=labels, columns=labels).to_csv(matrix_csv)
    _write_json(metrics_json, metrics)
    plot_written = False
    if os.environ.get("SECURITY_PIPELINE_SKIP_PLOTS") != "1":
        plot_written = _plot_confusion_matrix(matrix, labels, matrix_png, name)
    print_metrics(
        name=name,
        metrics=metrics,
        matrix=matrix,
        labels=labels,
        metrics_json=metrics_json,
        matrix_csv=matrix_csv,
        matrix_png=matrix_png if plot_written else None,
    )
    return metrics


def print_metrics(
    name: str,
    metrics: dict[str, Any],
    matrix: np.ndarray,
    labels: list[str],
    metrics_json: Path | None = None,
    matrix_csv: Path | None = None,
    matrix_png: Path | None = None,
) -> None:
    total = int(matrix.sum())
    correct = int(np.trace(matrix))
    incorrect = total - correct

    print(f"\n{'=' * 78}")
    print(f"{_section_title(name)}")
    print(f"{'=' * 78}")
    print(_section_explanation(name))
    print("")
    print("Ozet metrikler")
    print(f"- accuracy    : {metrics['accuracy']:.4f}  -> tum orneklerde dogru tahmin orani")
    print(f"- macro_f1    : {metrics['macro_f1']:.4f}  -> her sinifi esit agirlikta degerlendiren F1")
    print(f"- weighted_f1 : {metrics['weighted_f1']:.4f}  -> sinif destek sayisina gore agirlikli F1")
    loss = metrics.get("log_loss")
    if loss is not None:
        print(f"- log_loss    : {loss:.4f}  -> olasilik tahmin hatasi; dusuk olmasi daha iyi")
    else:
        print("- log_loss    : N/A")
    print(f"- ornek sayisi: {total}")
    print(f"- dogru/hata  : {correct} dogru, {incorrect} hatali")

    _print_binary_breakdown(name, matrix, labels)
    _print_classification_table(metrics)
    _print_top_confusions(matrix, labels)

    print("")
    print("Confusion matrix")
    print("Satirlar gercek sinifi, sutunlar modelin tahmin ettigi sinifi gosterir.")
    header = "true\\pred".ljust(24) + " ".join(label[:14].rjust(14) for label in labels)
    print(header)
    for label, row in zip(labels, matrix):
        print(label[:23].ljust(24) + " ".join(str(int(v)).rjust(14) for v in row))
    print("")
    print("Kaydedilen dosyalar")
    if metrics_json:
        print(f"- metrik JSON      : {metrics_json}")
    if matrix_csv:
        print(f"- confusion CSV    : {matrix_csv}")
    if matrix_png:
        print(f"- confusion PNG    : {matrix_png}")


def _write_json(path: Path, data: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _plot_confusion_matrix(
    matrix: np.ndarray,
    labels: list[str],
    output_path: Path,
    title: str,
) -> bool:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print(f"confusion matrix PNG kaydedilemedi: matplotlib kurulu degil ({output_path})")
        return False

    fig_width = max(7, len(labels) * 0.8)
    fig_height = max(6, len(labels) * 0.7)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    image = ax.imshow(matrix, interpolation="nearest", cmap="Blues")
    ax.figure.colorbar(image, ax=ax)
    ax.set(
        xticks=np.arange(len(labels)),
        yticks=np.arange(len(labels)),
        xticklabels=labels,
        yticklabels=labels,
        ylabel="True label",
        xlabel="Predicted label",
        title=title,
    )
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    threshold = matrix.max() / 2.0 if matrix.size else 0
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(
                j,
                i,
                str(int(matrix[i, j])),
                ha="center",
                va="center",
                color="white" if matrix[i, j] > threshold else "black",
                fontsize=8,
            )
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return True


def _section_title(name: str) -> str:
    if name.endswith("_binary"):
        return f"[{name}] Hiyerarsik adim 1: Binary saldiri tespiti"
    if name.endswith("_attack_type"):
        return f"[{name}] Hiyerarsik adim 2: Saldiri turu siniflandirma"
    if name.endswith("_risk"):
        return f"[{name}] Karar katmani: Nihai risk siniflandirma"
    if name.endswith("_safe_mode"):
        return f"[{name}] Karar katmani: Safe-mode siniflandirma"
    return f"[{name}] Model degerlendirme"


def _section_explanation(name: str) -> str:
    if name.endswith("_binary"):
        return (
            "Bu bolum modelin once 'attack var mi/yok mu' kararini olcer. "
            "Binary adim dogru calismazsa ikinci adimdaki tur tahmini tetiklenmez."
        )
    if name.endswith("_attack_type"):
        return (
            "Bu bolum sadece gercek attack ornekleri uzerinde saldiri turu tahminini olcer. "
            "Amac binary adimdan sonra tehdidin hangi tipe ait oldugunu ayirmaktir."
        )
    if name.endswith("_risk"):
        return (
            "Bu bolum CIC, CARLA ve nuScenes ozelliklerinden uretilen nihai risk kararini olcer."
        )
    if name.endswith("_safe_mode"):
        return (
            "Bu bolum karar katmaninin normal/monitoring/degraded/emergency mod secimini olcer."
        )
    return "Bu bolum modelin test veya validation performansini olcer."


def _print_binary_breakdown(name: str, matrix: np.ndarray, labels: list[str]) -> None:
    if not name.endswith("_binary") and not name.endswith("_risk"):
        return
    label_to_idx = {label: idx for idx, label in enumerate(labels)}
    negative = "0" if "0" in label_to_idx else "normal" if "normal" in label_to_idx else None
    positive = "1" if "1" in label_to_idx else "attack" if "attack" in label_to_idx else None
    if negative is None or positive is None:
        return

    tn = int(matrix[label_to_idx[negative], label_to_idx[negative]])
    fp = int(matrix[label_to_idx[negative], label_to_idx[positive]])
    fn = int(matrix[label_to_idx[positive], label_to_idx[negative]])
    tp = int(matrix[label_to_idx[positive], label_to_idx[positive]])
    print("")
    print("Binary karar detayi")
    print(f"- TP / dogru attack       : {tp}")
    print(f"- TN / dogru normal       : {tn}")
    print(f"- FP / normal iken attack : {fp}")
    print(f"- FN / attack iken normal : {fn}")


def _print_classification_table(metrics: dict[str, Any]) -> None:
    report = metrics.get("classification_report")
    if not isinstance(report, dict):
        return
    rows = []
    for label, values in report.items():
        if label in {"accuracy", "macro avg", "weighted avg"}:
            continue
        if not isinstance(values, dict):
            continue
        rows.append(
            (
                str(label),
                float(values.get("precision", 0.0)),
                float(values.get("recall", 0.0)),
                float(values.get("f1-score", 0.0)),
                int(values.get("support", 0)),
            )
        )
    if not rows:
        return

    print("")
    print("Sinif bazli performans")
    print("sinif".ljust(24) + "precision".rjust(12) + "recall".rjust(12) + "f1".rjust(12) + "support".rjust(12))
    for label, precision, recall, f1, support in rows:
        print(
            label[:23].ljust(24)
            + f"{precision:.4f}".rjust(12)
            + f"{recall:.4f}".rjust(12)
            + f"{f1:.4f}".rjust(12)
            + str(support).rjust(12)
        )


def _print_top_confusions(matrix: np.ndarray, labels: list[str], limit: int = 5) -> None:
    confusions: list[tuple[int, str, str]] = []
    for true_idx, true_label in enumerate(labels):
        for pred_idx, pred_label in enumerate(labels):
            if true_idx == pred_idx:
                continue
            count = int(matrix[true_idx, pred_idx])
            if count > 0:
                confusions.append((count, true_label, pred_label))
    confusions.sort(reverse=True)
    if not confusions:
        print("")
        print("En cok karisan sinif ciftleri: yok")
        return

    print("")
    print("En cok karisan sinif ciftleri")
    for count, true_label, pred_label in confusions[:limit]:
        print(f"- gercek={true_label} -> tahmin={pred_label}: {count} ornek")
