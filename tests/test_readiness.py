import numpy as np
import pandas as pd

from gb_ml.dq.readiness import (
    cold_start_report,
    correlation_leakage_candidates,
    feature_availability_audit,
    join_explosion_check,
    population_stability_index,
    rare_category_report,
    temporal_drift_report,
)


def test_rare_category_report_detecta_categoria_rara():
    df = pd.DataFrame({"categoria": ["A"] * 99 + ["B"]})
    report = rare_category_report(df, ["categoria"], min_frequency=0.02)

    row = report.iloc[0]
    assert row["categorias_raras"] == 1
    assert np.isclose(row["pct_linhas_categorias_raras"], 0.01)


def test_cold_start_report_sinaliza_poucas_observacoes():
    df = pd.DataFrame({
        "produto": ["A"] * 40 + ["B"] * 5,
        "data": pd.date_range("2025-01-01", periods=45),
    })

    report = cold_start_report(df, ["produto"], date_column="data", min_observations=30)
    flags = report.set_index("produto")["cold_start"].to_dict()

    assert not bool(flags["A"])
    assert bool(flags["B"])


def test_correlation_leakage_candidates_detecta_copia_do_target():
    df = pd.DataFrame({
        "target": [1, 2, 3, 4, 5],
        "leak": [1, 2, 3, 4, 5],
        "feature": [5, 1, 4, 2, 3],
    })

    report = correlation_leakage_candidates(df, "target", threshold=0.95)
    row = report.set_index("feature").loc["leak"]

    assert bool(row["leakage_candidate"])
    assert np.isclose(row["abs_correlacao"], 1.0)


def test_feature_availability_audit_bloqueia_feature_futura():
    cfg = {
        "preco": {"available_at_prediction": True},
        "vendas_realizadas": {"available_at_prediction": False},
    }

    report = feature_availability_audit(cfg, target="vendas")
    status = report.set_index("feature")["status"].to_dict()

    assert status["preco"] == "ok"
    assert status["vendas_realizadas"] == "risk"


def test_population_stability_index_proximo_de_zero_para_mesma_distribuicao():
    s = pd.Series(np.arange(1, 101))
    psi = population_stability_index(s, s.copy())

    assert psi < 1e-8


def test_temporal_drift_report_retorna_coluna_numerica():
    df = pd.DataFrame({
        "data": pd.date_range("2025-01-01", periods=100),
        "x": np.r_[np.arange(70), np.arange(30) + 100],
    })

    report = temporal_drift_report(df, "data", columns=["x"], recent_fraction=0.30)

    assert report.iloc[0]["coluna"] == "x"
    assert report.iloc[0]["nivel_drift"] in {"low", "moderate", "high", "insufficient_data"}


def test_join_explosion_check_detecta_crescimento():
    report = join_explosion_check(100, 130, max_growth_pct=0.05)

    assert report["status"] == "risk"
    assert np.isclose(report["growth_pct"], 0.30)
