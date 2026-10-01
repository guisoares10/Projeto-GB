import numpy as np
import pandas as pd

from gb_ml.profiling.visualization import (
    iqr_limits,
    iqr_outlier_mask,
    missingness_over_time,
    numeric_distribution_summary,
    seasonality_summary,
)


def test_iqr_limits_aplica_regra_de_tukey():
    series = pd.Series([1, 2, 3, 4, 100])

    limits = iqr_limits(series, multiplier=1.5)

    assert limits["q1"] == 2.0
    assert limits["q3"] == 4.0
    assert limits["iqr"] == 2.0
    assert limits["lower"] == -1.0
    assert limits["upper"] == 7.0


def test_iqr_outlier_mask_detecta_extremo():
    series = pd.Series([1, 2, 3, 4, 100])

    mask = iqr_outlier_mask(series)

    assert mask.tolist() == [False, False, False, False, True]


def test_numeric_distribution_summary_calcula_zeros_e_negativos():
    df = pd.DataFrame({"x": [-1, 0, 1, 2]})
    report = numeric_distribution_summary(df).set_index("coluna")

    assert np.isclose(report.loc["x", "zeros_pct"], 0.25)
    assert np.isclose(report.loc["x", "negativos_pct"], 0.25)


def test_missingness_over_time_detecta_mudanca_temporal():
    df = pd.DataFrame({
        "data": pd.to_datetime(["2025-01-01", "2025-01-15", "2025-02-01", "2025-02-15"]),
        "x": [1.0, 2.0, np.nan, np.nan],
    })

    report = missingness_over_time(df, "data", columns=["x"], freq="M")

    assert np.isclose(report.loc["2025-01", "x"], 0.0)
    assert np.isclose(report.loc["2025-02", "x"], 1.0)


def test_seasonality_summary_ordena_dias_da_semana():
    df = pd.DataFrame({
        "data": pd.to_datetime(["2025-01-06", "2025-01-07"]),
        "vendas": [10, 20],
    })

    report = seasonality_summary(df, "data", "vendas", component="day_of_week")

    assert report.iloc[0]["grupo"] == "Seg"
    assert report.iloc[1]["grupo"] == "Ter"
