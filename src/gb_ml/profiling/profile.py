"""Profiling genérico de DataFrames para EDA e data quality."""

from __future__ import annotations

import json
from typing import Iterable

import numpy as np
import pandas as pd

def _safe_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _semantic_type(series: pd.Series) -> str:
    """Infere um tipo semântico simples sem alterar a série."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"

    non_null = series.dropna()
    if non_null.empty:
        return "unknown"

    unique_ratio = non_null.nunique(dropna=True) / len(non_null)
    as_text = non_null.astype(str)
    avg_length = as_text.str.len().mean()

    if unique_ratio <= 0.05 or non_null.nunique(dropna=True) <= 30:
        return "categorical"
    if unique_ratio >= 0.95 and avg_length <= 80:
        return "identifier_or_high_cardinality"
    return "text"


def _coercion_candidate(series: pd.Series, threshold: float = 0.95) -> tuple[str | None, float]:
    """Detecta strings que parecem numéricas ou datas."""
    if not (pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)):
        return None, 0.0

    non_null = series.dropna()
    if non_null.empty:
        return None, 0.0

    text = non_null.astype(str).str.strip()
    text = text[text.ne("")]
    if text.empty:
        return None, 0.0

    numeric_rate = pd.to_numeric(text, errors="coerce").notna().mean()
    if numeric_rate >= threshold:
        return "numeric", float(numeric_rate)

    looks_date_like = text.str.contains(r"[-/:T]", regex=True).mean()
    if looks_date_like >= 0.5:
        parsed = pd.to_datetime(text, errors="coerce", format="mixed")
        date_rate = parsed.notna().mean()
        if date_rate >= threshold:
            return "datetime", float(date_rate)

    return None, max(float(numeric_rate), 0.0)


def profile_dataframe(
    df: pd.DataFrame,
    *,
    top_n: int = 5,
    coercion_threshold: float = 0.95,
) -> pd.DataFrame:
    """Cria um perfil por coluna com estatísticas úteis para EDA."""
    n_rows = len(df)
    records: list[dict[str, object]] = []

    for column in df.columns:
        s = df[column]
        non_null = s.dropna()
        n_null = int(s.isna().sum())
        n_unique = int(s.nunique(dropna=True))
        blank_count = 0
        min_value = max_value = mean = std = p01 = p25 = p50 = p75 = p99 = None

        if pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s):
            blank_count = int(s.dropna().astype(str).str.strip().eq("").sum())

        if pd.api.types.is_numeric_dtype(s):
            numeric = pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan)
            valid = numeric.dropna()
            if not valid.empty:
                q = valid.quantile([0.01, 0.25, 0.50, 0.75, 0.99])
                min_value = valid.min()
                max_value = valid.max()
                mean = valid.mean()
                std = valid.std()
                p01, p25, p50, p75, p99 = (q.loc[x] for x in [0.01, 0.25, 0.50, 0.75, 0.99])
        elif pd.api.types.is_datetime64_any_dtype(s):
            if not non_null.empty:
                min_value = non_null.min()
                max_value = non_null.max()

        top_values = non_null.astype(str).value_counts(dropna=False).head(top_n).to_dict()
        candidate_type, coercion_rate = _coercion_candidate(s, coercion_threshold)

        records.append({
            "coluna": column,
            "dtype": str(s.dtype),
            "tipo_semantico": _semantic_type(s),
            "linhas": n_rows,
            "nulos": n_null,
            "pct_nulos": (n_null / n_rows) if n_rows else 0.0,
            "vazios_string": blank_count,
            "unicos": n_unique,
            "pct_unicos": (n_unique / max(len(non_null), 1)),
            "constante": bool(n_unique <= 1 and len(non_null) > 0),
            "tipo_candidato": candidate_type,
            "taxa_conversao_tipo": coercion_rate,
            "min": min_value,
            "p01": p01,
            "p25": p25,
            "mediana": p50,
            "p75": p75,
            "p99": p99,
            "max": max_value,
            "media": mean,
            "desvio_padrao": std,
            "top_valores": _safe_json(top_values),
        })

    return pd.DataFrame.from_records(records)


def outlier_report(
    df: pd.DataFrame,
    columns: Iterable[str] | None = None,
    *,
    method: str = "mad",
    threshold: float = 3.5,
    iqr_multiplier: float = 1.5,
) -> pd.DataFrame:
    """Resume outliers de colunas numéricas por MAD ou IQR."""
    numeric_columns = list(columns) if columns is not None else list(df.select_dtypes(include=np.number).columns)
    records: list[dict[str, object]] = []

    for column in numeric_columns:
        if column not in df.columns:
            continue

        s = pd.to_numeric(df[column], errors="coerce").replace([np.inf, -np.inf], np.nan)
        valid = s.dropna()
        lower = upper = None

        if valid.empty:
            count = 0
        elif method.lower() == "mad":
            median = valid.median()
            mad = np.median(np.abs(valid - median))
            if mad == 0 or np.isnan(mad):
                count = 0
            else:
                robust_z = 0.6745 * (s - median) / mad
                count = int((robust_z.abs() > threshold).fillna(False).sum())
        elif method.lower() == "iqr":
            q1, q3 = valid.quantile([0.25, 0.75])
            iqr = q3 - q1
            lower = q1 - iqr_multiplier * iqr
            upper = q3 + iqr_multiplier * iqr
            count = int(((s < lower) | (s > upper)).fillna(False).sum())
        else:
            raise ValueError("method deve ser 'mad' ou 'iqr'")

        records.append({
            "coluna": column,
            "metodo": method.lower(),
            "outliers": count,
            "pct_outliers": count / len(df) if len(df) else 0.0,
            "limite_inferior": lower,
            "limite_superior": upper,
            "threshold": threshold if method.lower() == "mad" else iqr_multiplier,
        })

    columns_schema = [
        "coluna",
        "metodo",
        "outliers",
        "pct_outliers",
        "limite_inferior",
        "limite_superior",
        "threshold",
    ]
    return pd.DataFrame.from_records(records, columns=columns_schema)


def temporal_summary(
    df: pd.DataFrame,
    date_column: str,
    *,
    group_columns: Iterable[str] | None = None,
    freq: str = "D",
) -> pd.DataFrame:
    """Resume cobertura temporal e quantidade de períodos faltantes por grupo."""
    if date_column not in df.columns:
        raise KeyError(f"Coluna de data ausente: {date_column}")

    groups = list(group_columns or [])
    work = df[[*groups, date_column]].copy()
    work[date_column] = pd.to_datetime(work[date_column], errors="coerce")
    work = work.dropna(subset=[date_column])

    def summarize(part: pd.DataFrame) -> pd.Series:
        dates = part[date_column].drop_duplicates().sort_values()
        if dates.empty:
            return pd.Series({"data_min": pd.NaT, "data_max": pd.NaT, "periodos_observados": 0, "periodos_esperados": 0, "periodos_faltantes": 0})
        expected = pd.date_range(dates.min(), dates.max(), freq=freq)
        missing = expected.difference(pd.DatetimeIndex(dates))
        return pd.Series({
            "data_min": dates.min(),
            "data_max": dates.max(),
            "periodos_observados": len(dates),
            "periodos_esperados": len(expected),
            "periodos_faltantes": len(missing),
        })

    if groups:
        return work.groupby(groups, dropna=False).apply(summarize, include_groups=False).reset_index()
    return summarize(work).to_frame().T


def infer_date_columns(
    df: pd.DataFrame,
    *,
    bq_schema: pd.DataFrame | None = None,
    parse_threshold: float = 0.95,
) -> list[str]:
    """Identifica colunas temporais por schema do BigQuery, dtype ou parseabilidade."""
    candidates: list[str] = []

    if bq_schema is not None and not bq_schema.empty:
        type_col = "field_type" if "field_type" in bq_schema.columns else None
        name_col = "name" if "name" in bq_schema.columns else None
        if type_col and name_col:
            temporal_types = {"DATE", "DATETIME", "TIMESTAMP"}
            for _, row in bq_schema.iterrows():
                if str(row[type_col]).upper() in temporal_types:
                    name = str(row[name_col])
                    if name in df.columns and name not in candidates:
                        candidates.append(name)

    for column in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[column]) and column not in candidates:
            candidates.append(column)

    # Fallback para DATE do BigQuery que eventualmente chega como object/dbdate.
    for column in df.columns:
        if column in candidates:
            continue
        s = df[column].dropna()
        if s.empty:
            continue
        if not (
            pd.api.types.is_object_dtype(s)
            or pd.api.types.is_string_dtype(s)
        ):
            continue

        sample = s.head(500)
        parsed = pd.to_datetime(sample, errors="coerce")
        parse_rate = parsed.notna().mean()
        if parse_rate >= parse_threshold:
            candidates.append(column)

    return candidates


def resolve_date_column(
    df: pd.DataFrame,
    *,
    configured: str | None = None,
    bq_schema: pd.DataFrame | None = None,
) -> tuple[str | None, list[str], str]:
    """Resolve a coluna temporal principal e informa a origem da decisão."""
    if configured and configured in df.columns:
        return configured, [configured], "config"

    candidates = infer_date_columns(df, bq_schema=bq_schema)
    if not candidates:
        return None, [], "not_found"

    if len(candidates) == 1:
        return candidates[0], candidates, "inferred_type"

    # Desempate por nomes que normalmente representam a data do fato.
    hints = (
        "data",
        "date",
        "dt",
        "semana",
        "week",
        "mes",
        "month",
        "dia",
        "day",
        "timestamp",
    )
    scored = []
    for column in candidates:
        normalized = column.lower()
        score = sum(1 for hint in hints if hint in normalized)
        scored.append((score, column))

    scored.sort(key=lambda x: (-x[0], candidates.index(x[1])))
    if scored and scored[0][0] > 0:
        return scored[0][1], candidates, "inferred_type_name_hint"

    return candidates[0], candidates, "inferred_type_first_candidate"
