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

    columns_schema = [
        "coluna",
        "n_validos",
        "outliers",
        "pct_outliers",
        "q1",
        "q3",
        "iqr",
        "limite_inferior",
        "limite_superior",
        "min_outlier",
        "max_outlier",
    ]
    return pd.DataFrame(summaries, columns=columns_schema)


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
    if ordered.empty:
        ax.text(
            0.5,
            0.5,
            "Nenhuma variável numérica elegível para análise de outliers.",
            ha="center",
            va="center",
            transform=ax.transAxes,
        )
        ax.set_axis_off()
        fig.tight_layout()
        return fig, ax
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


def numeric_distribution_summary(
    df: pd.DataFrame,
    columns: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Resume forma das distribuições numéricas para o EDA."""
    numeric_columns = list(columns) if columns is not None else list(df.select_dtypes(include=np.number).columns)
    records: list[dict[str, object]] = []

    for column in numeric_columns:
        if column not in df.columns:
            continue
        s = pd.to_numeric(df[column], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        if s.empty:
            continue

        q = s.quantile([0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99])
        records.append({
            "coluna": column,
            "n": int(s.size),
            "media": float(s.mean()),
            "mediana": float(s.median()),
            "desvio_padrao": float(s.std()),
            "skewness": float(s.skew()),
            "kurtosis": float(s.kurt()),
            "p01": float(q.loc[0.01]),
            "p05": float(q.loc[0.05]),
            "p25": float(q.loc[0.25]),
            "p50": float(q.loc[0.50]),
            "p75": float(q.loc[0.75]),
            "p95": float(q.loc[0.95]),
            "p99": float(q.loc[0.99]),
            "zeros_pct": float((s == 0).mean()),
            "negativos_pct": float((s < 0).mean()),
        })

    return pd.DataFrame.from_records(records)


def plot_numeric_distributions(
    df: pd.DataFrame,
    columns: Iterable[str] | None = None,
    *,
    bins: int = 30,
    figsize: tuple[float, float] = (9, 4),
) -> pd.DataFrame:
    """Plota um histograma por variável numérica e retorna o resumo estatístico."""
    import matplotlib.pyplot as plt

    summary = numeric_distribution_summary(df, columns)
    for column in summary["coluna"].tolist():
        s = pd.to_numeric(df[column], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()

        fig, ax = plt.subplots(figsize=figsize)
        ax.hist(s, bins=bins)
        ax.axvline(s.median(), linestyle="--", linewidth=1.5, label="Mediana")
        ax.axvline(s.mean(), linestyle=":", linewidth=1.5, label="Média")
        ax.set_title(f"Distribuição — {column}")
        ax.set_xlabel(column)
        ax.set_ylabel("Frequência")
        ax.legend()
        fig.tight_layout()
        plt.show()
        plt.close(fig)

    return summary


def missingness_over_time(
    df: pd.DataFrame,
    date_column: str,
    *,
    columns: Iterable[str] | None = None,
    freq: str = "MS",
) -> pd.DataFrame:
    """Calcula percentual de nulos por período e por variável."""
    if date_column not in df.columns:
        raise KeyError(f"Coluna de data ausente: {date_column}")

    work = df.copy()
    work[date_column] = pd.to_datetime(work[date_column], errors="coerce")
    work = work.dropna(subset=[date_column])

    selected = list(columns) if columns is not None else [c for c in work.columns if c != date_column]
    selected = [c for c in selected if c in work.columns]

    if work.empty or not selected:
        return pd.DataFrame()

    period = work[date_column].dt.to_period(freq.replace("S", "") if freq.endswith("S") else freq)
    result = work[selected].isna().groupby(period).mean()
    result.index = result.index.astype(str)
    result.index.name = "periodo"
    return result


def plot_missingness_over_time(
    df: pd.DataFrame,
    date_column: str,
    *,
    columns: Iterable[str] | None = None,
    freq: str = "M",
    figsize: tuple[float, float] = (11, 5),
):
    """Plota heatmap simples de percentual de nulos por período."""
    import matplotlib.pyplot as plt

    summary = missingness_over_time(df, date_column, columns=columns, freq=freq)
    if summary.empty:
        raise ValueError("Não há dados suficientes para visualizar missingness temporal.")

    fig, ax = plt.subplots(figsize=figsize)
    image = ax.imshow(summary.T.to_numpy() * 100, aspect="auto")
    ax.set_title("% de nulos por variável ao longo do tempo")
    ax.set_xlabel("Período")
    ax.set_ylabel("Variável")
    ax.set_xticks(range(len(summary.index)))
    ax.set_xticklabels(summary.index, rotation=45, ha="right")
    ax.set_yticks(range(len(summary.columns)))
    ax.set_yticklabels(summary.columns)
    cbar = fig.colorbar(image, ax=ax)
    cbar.set_label("% nulos")
    fig.tight_layout()
    return fig, ax, summary


def plot_target_time_series(
    df: pd.DataFrame,
    date_column: str,
    target: str,
    *,
    rolling_windows: tuple[int, ...] = (7, 28),
    agg: str = "sum",
    figsize: tuple[float, float] = (11, 4),
):
    """Plota série temporal agregada do target e médias móveis."""
    import matplotlib.pyplot as plt

    if date_column not in df.columns or target not in df.columns:
        raise KeyError("date_column e target precisam existir no DataFrame.")

    work = df[[date_column, target]].copy()
    work[date_column] = pd.to_datetime(work[date_column], errors="coerce")
    work[target] = pd.to_numeric(work[target], errors="coerce")
    work = work.dropna(subset=[date_column, target])

    if agg == "sum":
        series = work.groupby(date_column)[target].sum().sort_index()
    elif agg == "mean":
        series = work.groupby(date_column)[target].mean().sort_index()
    else:
        raise ValueError("agg deve ser 'sum' ou 'mean'.")

    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(series.index, series.values, label=target)

    for window in rolling_windows:
        if window > 1:
            ax.plot(series.index, series.rolling(window, min_periods=1).mean(), label=f"Média móvel {window}")

    ax.set_title(f"Evolução temporal — {target}")
    ax.set_xlabel("Data")
    ax.set_ylabel(target)
    ax.legend()
    fig.tight_layout()
    return fig, ax, series


def seasonality_summary(
    df: pd.DataFrame,
    date_column: str,
    target: str,
    *,
    component: str = "day_of_week",
    agg: str = "mean",
) -> pd.DataFrame:
    """Resume target por componente de calendário."""
    work = df[[date_column, target]].copy()
    work[date_column] = pd.to_datetime(work[date_column], errors="coerce")
    work[target] = pd.to_numeric(work[target], errors="coerce")
    work = work.dropna()

    if component == "day_of_week":
        labels = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        work["grupo"] = pd.Categorical(
            work[date_column].dt.dayofweek.map(dict(enumerate(labels))),
            categories=labels,
            ordered=True,
        )
    elif component == "month":
        labels = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        work["grupo"] = pd.Categorical(
            work[date_column].dt.month.map(dict(enumerate(labels, start=1))),
            categories=labels,
            ordered=True,
        )
    else:
        raise ValueError("component deve ser 'day_of_week' ou 'month'.")

    grouped = work.groupby("grupo", observed=False)[target]
    values = grouped.mean() if agg == "mean" else grouped.sum()
    return values.rename(target).reset_index()


def plot_seasonality(
    df: pd.DataFrame,
    date_column: str,
    target: str,
    *,
    component: str = "day_of_week",
    agg: str = "mean",
    figsize: tuple[float, float] = (9, 4),
):
    """Plota sazonalidade média ou total por componente de calendário."""
    import matplotlib.pyplot as plt

    summary = seasonality_summary(df, date_column, target, component=component, agg=agg)
    fig, ax = plt.subplots(figsize=figsize)
    ax.bar(summary["grupo"].astype(str), summary[target])
    label = "dia da semana" if component == "day_of_week" else "mês"
    ax.set_title(f"Sazonalidade de {target} por {label}")
    ax.set_xlabel(label.capitalize())
    ax.set_ylabel(f"{agg} de {target}")
    fig.tight_layout()
    return fig, ax, summary


def plot_correlation_heatmap(
    df: pd.DataFrame,
    *,
    method: str = "spearman",
    figsize: tuple[float, float] = (8, 6),
):
    """Plota matriz de correlação das variáveis numéricas."""
    import matplotlib.pyplot as plt

    corr = df.select_dtypes(include=np.number).corr(method=method)
    if corr.empty:
        raise ValueError("Não há variáveis numéricas suficientes para correlação.")

    fig, ax = plt.subplots(figsize=figsize)
    image = ax.imshow(corr.to_numpy(), vmin=-1, vmax=1)
    ax.set_title(f"Correlação {method.title()}")
    ax.set_xticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(corr.index)))
    ax.set_yticklabels(corr.index)

    for i in range(len(corr.index)):
        for j in range(len(corr.columns)):
            value = corr.iloc[i, j]
            if pd.notna(value):
                ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=8)

    cbar = fig.colorbar(image, ax=ax)
    cbar.set_label("Correlação")
    fig.tight_layout()
    return fig, ax, corr
