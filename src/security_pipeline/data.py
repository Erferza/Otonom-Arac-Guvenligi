from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


COMMON_BINARY_LABELS = (
    "binary_label",
    "Label",
    "label",
    "Attack",
    "attack",
    "is_attack",
    "benign",
)
COMMON_MULTICLASS_LABELS = (
    "multiclass_label",
    "attack_type",
    "type",
    "category",
    "Attack_type",
    "Attack",
)


def read_table(path: Path, max_rows: int | None = None) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path, nrows=max_rows)
    if suffix == ".parquet":
        try:
            if max_rows is not None:
                import pyarrow.parquet as pq

                batches = pq.ParquetFile(path).iter_batches(batch_size=max_rows)
                return next(batches).to_pandas()
            df = pd.read_parquet(path)
        except ImportError as exc:
            raise RuntimeError(
                "Parquet dosyasini okumak icin pyarrow veya fastparquet gerekli. "
                "`python3 -m pip install -r requirements.txt` komutunu calistirin."
            ) from exc
        except StopIteration:
            return pd.DataFrame()
        if max_rows is not None:
            return df.head(max_rows)
        return df
    raise ValueError(f"Desteklenmeyen tablo formati: {path}")


def find_label_column(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    lower_to_original = {c.lower(): c for c in df.columns}
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
        if candidate.lower() in lower_to_original:
            return lower_to_original[candidate.lower()]
    return None


def infer_binary_label(df: pd.DataFrame) -> str | None:
    return find_label_column(df, COMMON_BINARY_LABELS)


def infer_multiclass_label(df: pd.DataFrame) -> str | None:
    return find_label_column(df, COMMON_MULTICLASS_LABELS)


def normalize_binary_labels(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return (series.astype(float) > 0).astype(int)
    values = series.astype(str).str.strip().str.lower()
    benign = {"0", "normal", "benign", "false", "no", "none"}
    return (~values.isin(benign)).astype(int)


def balanced_sample(
    df: pd.DataFrame,
    label_column: str,
    max_rows: int | None,
    random_state: int = 42,
) -> pd.DataFrame:
    if max_rows is None or len(df) <= max_rows:
        return df
    groups = list(df.groupby(label_column, group_keys=False))
    per_group = max(1, max_rows // len(groups))
    sampled = [
        group.sample(n=min(len(group), per_group), random_state=random_state)
        for _, group in groups
    ]
    result = pd.concat(sampled, axis=0)
    remaining = max_rows - len(result)
    if remaining > 0:
        rest = df.drop(index=result.index)
        if not rest.empty:
            result = pd.concat(
                [result, rest.sample(n=min(remaining, len(rest)), random_state=random_state)]
            )
    if len(result) > max_rows:
        result = result.sample(n=max_rows, random_state=random_state)
    return result.sample(frac=1.0, random_state=random_state).reset_index(drop=True)


def load_json(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
