"""Visualizações reutilizáveis para EDA."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd


def iqr_limits(
    series: pd.Series,
    *,
    multiplier: float = 1.5,
) -> dict[str, float]:
    """Calcula quartis, IQR e limites de Tukey para uma série numérica."""
    s = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()

    if s.empty:
        return {
            "q1": np.nan,
            "q3": np.nan,
            "iqr": np.nan,
            "lower": np.nan,
            "upper": np.nan,
        }

    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    return {
        "q1": float(q1),
        "q3": float(q3),
        "iqr": float(iqr),
        "lower": float(q1 - multiplier * iqr),
        "upper": float(q3 + multiplier * iqr),
    }


def iqr_outlier_mask(
    series: pd.Series,
    *,
    multiplier: float = 1.5,
) -> pd.Series:
    """Retorna máscara booleana de outliers segundo a regra de Tukey/IQR."""
    numeric = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan)
    limits = iqr_limits(numeric, multiplier=multiplier)

    if np.isnan(limits["lower"]) or np.isnan(limits["upper"]):
        return pd.Series(False, index=series.index)

    return ((numeric < limits["lower"]) | (numeric > limits["upper"])).fillna(False)


def plot_outlier_boxplot(
    df: pd.DataFrame,
    column: str,
    *,
    iqr_multiplier: float = 1.5,
    figsize: tuple[float, float] = (10, 2.8),
):
    """Plota boxplot horizontal e retorna figura, eixo e resumo dos outliers."""
    import matplotlib.pyplot as plt

    if column not in df.columns:
        raise KeyError(f"Coluna ausente: {column}")

    numeric = pd.to_numeric(df[column], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if numeric.empty:
        raise ValueError(f"A coluna '{column}' não possui valores numéricos válidos.")

    limits = iqr_limits(numeric, multiplier=iqr_multiplier)
    mask = iqr_outlier_mask(df[column], multiplier=iqr_multiplier)
    outliers = pd.to_numeric(df.loc[mask, column], errors="coerce").dropna()

    fig, ax = plt.subplots(figsize=figsize)
    ax.boxplot(
        numeric,
        vert=False,
        whis=iqr_multiplier,
        showfliers=True,
    )
    ax.set_title(f"Boxplot — {column}")
    ax.set_xlabel(column)
    ax.set_yticks([])

    summary = {
        "coluna": column,
        "n_validos": int(len(numeric)),
        "outliers": int(mask.sum()),
        "pct_outliers": float(mask.mean()) if len(mask) else 0.0,
        "q1": limits["q1"],
        "q3": limits["q3"],
        "iqr": limits["iqr"],
        "limite_inferior": limits["lower"],
        "limite_superior": limits["upper"],
        "min_outlier": float(outliers.min()) if not outliers.empty else np.nan,
        "max_outlier": float(outliers.max()) if not outliers.empty else np.nan,
    }

    fig.tight_layout()
    return fig, ax, summary


def plot_outlier_boxplots(
    df: pd.DataFrame,
    columns: Iterable[str] | None = None,
    *,
    iqr_multiplier: float = 1.5,
) -> pd.DataFrame:
    """Plota um boxplot por coluna numérica e devolve o resumo consolidado."""
    import matplotlib.pyplot as plt

    numeric_columns = (
        list(columns)
        if columns is not None
        else list(df.select_dtypes(include=np.number).columns)
    )

    summaries: list[dict[str, object]] = []

    for column in numeric_columns:
        fig, _, summary = plot_outlier_boxplot(
            df,
            column,
            iqr_multiplier=iqr_multiplier,
        )
        summaries.append(summary)
        plt.show()
        plt.close(fig)

    return pd.DataFrame(summaries)


def plot_outlier_rate(
    report: pd.DataFrame,
    *,
    figsize: tuple[float, float] = (10, 4),
):
    """Plota percentual de outliers por coluna a partir do outlier_report."""
    import matplotlib.pyplot as plt

    required = {"coluna", "pct_outliers"}
    missing = required.difference(report.columns)
    if missing:
        raise ValueError(f"Colunas ausentes no report: {sorted(missing)}")

    ordered = report.sort_values("pct_outliers", ascending=True).copy()

    fig, ax = plt.subplots(figsize=figsize)
    ax.barh(ordered["coluna"].astype(str), ordered["pct_outliers"] * 100)
    ax.set_title("Percentual de outliers por variável")
    ax.set_xlabel("% de observações classificadas como outlier")
    ax.set_ylabel("Variável")

    for patch, value in zip(ax.patches, ordered["pct_outliers"] * 100):
        ax.text(
            patch.get_width(),
            patch.get_y() + patch.get_height() / 2,
            f" {value:.2f}%",
            va="center",
        )

    fig.tight_layout()
    return fig, ax
