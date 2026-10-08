"""Diagnósticos de ML Readiness para datasets tabulares e temporais."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


import numpy as np
import pandas as pd


def rare_category_report(
    df: pd.DataFrame,
    columns: Iterable[str] | None = None,
    *,
    min_frequency: float = 0.01,
) -> pd.DataFrame:
    """Resume categorias raras e a parcela de linhas afetadas."""
    if not 0 < min_frequency < 1:
        raise ValueError("min_frequency deve estar entre 0 e 1.")

    if columns is None:
        columns = [
            c for c in df.columns
            if (
                pd.api.types.is_object_dtype(df[c])
                or pd.api.types.is_string_dtype(df[c])
                or isinstance(df[c].dtype, pd.CategoricalDtype)
            )
        ]

    records: list[dict[str, object]] = []
    n_rows = len(df)

    for column in columns:
        if column not in df.columns:
            continue
        s = df[column]
        counts = s.value_counts(dropna=False)
        frequencies = counts / max(n_rows, 1)
        rare = frequencies[frequencies < min_frequency]

        records.append({
            "coluna": column,
            "categorias": int(counts.size),
            "categorias_raras": int(rare.size),
            "pct_categorias_raras": float(rare.size / counts.size) if counts.size else 0.0,
            "linhas_em_categorias_raras": int(counts.loc[rare.index].sum()) if not rare.empty else 0,
            "pct_linhas_categorias_raras": float(counts.loc[rare.index].sum() / n_rows) if n_rows and not rare.empty else 0.0,
            "categoria_mais_frequente_pct": float(frequencies.iloc[0]) if not frequencies.empty else 0.0,
            "limite_frequencia": min_frequency,
        })

    return pd.DataFrame.from_records(records)


def cold_start_report(
    df: pd.DataFrame,
    entity_columns: Iterable[str],
    *,
    date_column: str | None = None,
    min_observations: int = 30,
    min_history_days: int | None = None,
) -> pd.DataFrame:
    """Identifica séries/entidades com histórico potencialmente insuficiente."""
    entity_columns = list(entity_columns)
    missing = [c for c in entity_columns if c not in df.columns]
    if missing:
        raise KeyError(f"Colunas de entidade ausentes: {missing}")
    if min_observations <= 0:
        raise ValueError("min_observations deve ser maior que zero.")

    work = df.copy()
    if date_column is not None:
        if date_column not in work.columns:
            raise KeyError(f"Coluna de data ausente: {date_column}")
        work[date_column] = pd.to_datetime(work[date_column], errors="coerce")

    grouped = work.groupby(entity_columns, dropna=False)
    report = grouped.size().rename("observacoes").reset_index()

    if date_column is not None:
        dates = grouped[date_column].agg(["min", "max"]).reset_index()
        dates = dates.rename(columns={"min": "data_min", "max": "data_max"})
        report = report.merge(dates, on=entity_columns, how="left")
        report["dias_historico"] = (report["data_max"] - report["data_min"]).dt.days + 1

    insufficient = report["observacoes"] < min_observations
    if min_history_days is not None and "dias_historico" in report.columns:
        insufficient = insufficient | (report["dias_historico"] < min_history_days)

    report["cold_start"] = insufficient
    return report.sort_values(["cold_start", "observacoes"], ascending=[False, True]).reset_index(drop=True)


def correlation_leakage_candidates(
    df: pd.DataFrame,
    target: str,
    *,
    threshold: float = 0.95,
    method: str = "spearman",
) -> pd.DataFrame:
    """Sinaliza correlações muito altas com o target para investigação de leakage."""
    if target not in df.columns:
        raise KeyError(f"Target ausente: {target}")
    if not 0 < threshold <= 1:
        raise ValueError("threshold deve estar entre 0 e 1.")

    numeric = df.select_dtypes(include=np.number)
    if target not in numeric.columns:
        return pd.DataFrame(columns=["feature", "correlacao", "abs_correlacao", "leakage_candidate"])

    corr = numeric.corr(method=method)[target].drop(labels=[target], errors="ignore").dropna()
    report = corr.rename("correlacao").reset_index().rename(columns={"index": "feature"})
    report["abs_correlacao"] = report["correlacao"].abs()
    report["leakage_candidate"] = report["abs_correlacao"] >= threshold
    return report.sort_values("abs_correlacao", ascending=False).reset_index(drop=True)


def feature_availability_audit(
    feature_config: dict[str, Any] | None,
    *,
    target: str | None = None,
) -> pd.DataFrame:
    """Audita disponibilidade das features no instante da previsão."""
    feature_config = feature_config or {}
    records: list[dict[str, object]] = []

    for feature, rules in feature_config.items():
        if isinstance(rules, bool):
            available = rules
            detail = ""
        else:
            rules = rules or {}
            available = bool(rules.get("available_at_prediction", False))
            detail = str(rules.get("detail", ""))

        risk = (feature == target) or not available
        reason = "target não pode ser feature" if feature == target else (
            "não disponível no instante da previsão" if not available else ""
        )

        records.append({
            "feature": feature,
            "disponivel_na_previsao": available,
            "status": "risk" if risk else "ok",
            "motivo": reason or detail,
        })

    return pd.DataFrame.from_records(records)


def population_stability_index(
    expected: pd.Series,
    actual: pd.Series,
    *,
    bins: int = 10,
    epsilon: float = 1e-6,
) -> float:
    """Calcula PSI para duas amostras numéricas usando bins derivados da referência."""
    ref = pd.to_numeric(expected, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    cur = pd.to_numeric(actual, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()

    if ref.empty or cur.empty:
        return np.nan

    quantiles = np.unique(ref.quantile(np.linspace(0, 1, bins + 1)).to_numpy(dtype=float))
    if quantiles.size < 3:
        return 0.0 if ref.equals(cur) else np.nan

    quantiles[0] = -np.inf
    quantiles[-1] = np.inf

    ref_bins = pd.cut(ref, bins=quantiles, include_lowest=True, duplicates="drop")
    cur_bins = pd.cut(cur, bins=quantiles, include_lowest=True, duplicates="drop")

    ref_pct = ref_bins.value_counts(normalize=True, sort=False)
    cur_pct = cur_bins.value_counts(normalize=True, sort=False).reindex(ref_pct.index, fill_value=0.0)

    ref_pct = ref_pct.clip(lower=epsilon)
    cur_pct = cur_pct.clip(lower=epsilon)

    return float(((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)).sum())


def temporal_drift_report(
    df: pd.DataFrame,
    date_column: str,
    *,
    columns: Iterable[str] | None = None,
    split_date: str | pd.Timestamp | None = None,
    recent_fraction: float = 0.30,
    bins: int = 10,
) -> pd.DataFrame:
    """Compara período histórico versus recente usando PSI em variáveis numéricas."""
    if date_column not in df.columns:
        raise KeyError(f"Coluna de data ausente: {date_column}")

    work = df.copy()
    work[date_column] = pd.to_datetime(work[date_column], errors="coerce")
    work = work.dropna(subset=[date_column]).sort_values(date_column)
    if work.empty:
        return pd.DataFrame()

    if split_date is None:
        if not 0 < recent_fraction < 1:
            raise ValueError("recent_fraction deve estar entre 0 e 1.")
        split_idx = max(1, int(len(work) * (1 - recent_fraction)))
        split_idx = min(split_idx, len(work) - 1)
        split_ts = work.iloc[split_idx][date_column]
    else:
        split_ts = pd.Timestamp(split_date)

    historical = work[work[date_column] < split_ts]
    recent = work[work[date_column] >= split_ts]

    numeric_columns = list(columns) if columns is not None else list(work.select_dtypes(include=np.number).columns)
    records: list[dict[str, object]] = []

    for column in numeric_columns:
        if column not in work.columns:
            continue
        psi = population_stability_index(historical[column], recent[column], bins=bins)
        if np.isnan(psi):
            level = "insufficient_data"
        elif psi < 0.10:
            level = "low"
        elif psi < 0.25:
            level = "moderate"
        else:
            level = "high"

        records.append({
            "coluna": column,
            "psi": psi,
            "nivel_drift": level,
            "split_date": split_ts,
            "linhas_historico": len(historical),
            "linhas_recente": len(recent),
        })

    return pd.DataFrame.from_records(records).sort_values("psi", ascending=False, na_position="last")


def join_explosion_check(
    rows_before: int,
    rows_after: int,
    *,
    max_growth_pct: float = 0.0,
) -> dict[str, float | int | str | bool]:
    """Sinaliza crescimento inesperado de linhas após um JOIN."""
    if rows_before < 0 or rows_after < 0:
        raise ValueError("Contagens de linhas não podem ser negativas.")

    growth_ratio = rows_after / rows_before if rows_before else np.nan
    growth_pct = (growth_ratio - 1) if rows_before else np.nan
    exploded = bool(rows_before and growth_pct > max_growth_pct)

    return {
        "rows_before": rows_before,
        "rows_after": rows_after,
        "growth_ratio": growth_ratio,
        "growth_pct": growth_pct,
        "status": "risk" if exploded else "ok",
        "max_growth_pct": max_growth_pct,
    }
