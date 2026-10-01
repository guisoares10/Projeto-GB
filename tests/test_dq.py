import pandas as pd

from gb_ml.dq.checks import quality_gate, run_quality_checks


def test_quality_gate_bloqueia_duplicidade_no_grao():
    df = pd.DataFrame(
        {
            "data": pd.to_datetime(["2025-01-01", "2025-01-01"]),
            "produto_id": ["A", "A"],
            "vendas": [10.0, 12.0],
        }
    )
    config = {
        "grain": ["data", "produto_id"],
        "columns": {
            "data": {"type": "datetime", "nullable": False},
            "produto_id": {"type": "string", "nullable": False},
            "vendas": {"type": "numeric", "nullable": False, "min": 0},
        },
    }

    report = run_quality_checks(df, config)
    approved, critical = quality_gate(report)

    assert not approved
    assert "grao_unico" in set(critical["check"])


def test_limite_minimo_detecta_venda_negativa():
    df = pd.DataFrame({"vendas": [10.0, -1.0, 3.0]})
    config = {"columns": {"vendas": {"type": "numeric", "nullable": False, "min": 0}}}

    report = run_quality_checks(df, config)
    row = report[(report["check"] == "limite_minimo") & (report["coluna"] == "vendas")].iloc[0]

    assert row["status"] == "fail"
    assert row["metrica"] == 1
