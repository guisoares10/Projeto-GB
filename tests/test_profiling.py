import pandas as pd

from gb_ml.profiling.profile import outlier_report, profile_dataframe, temporal_summary


def test_profile_detecta_string_numerica_e_constante():
    df = pd.DataFrame(
        {
            "numero_como_texto": ["1", "2", "3", "4"],
            "constante": ["x", "x", "x", "x"],
        }
    )

    profile = profile_dataframe(df).set_index("coluna")

    assert profile.loc["numero_como_texto", "tipo_candidato"] == "numeric"
    assert bool(profile.loc["constante", "constante"])


def test_outlier_report_mad_detecta_valor_extremo():
    df = pd.DataFrame({"x": [10, 11, 9, 10, 10, 11, 500]})
    report = outlier_report(df, method="mad")

    assert report.loc[0, "outliers"] >= 1


def test_temporal_summary_detecta_gap():
    df = pd.DataFrame({"data": pd.to_datetime(["2025-01-01", "2025-01-03"])})
    report = temporal_summary(df, "data")

    assert report.loc[0, "periodos_faltantes"] == 1
