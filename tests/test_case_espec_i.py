import pandas as pd

from gb_ml.case_espec_i import (
    aggregate_daily,
    prepare_case_data,
    quality_summary,
    weekday_summary,
)


def _sample():
    return pd.DataFrame({
        "dt_hr_venda": [
            "2025-11-01T00:00:00",
            "2025-11-01T01:00:00",
            "2025-11-02T00:00:00",
        ],
        "des_canal_venda_final_agrup": ["Site", "App", "Site"],
        "des_categoria_material": ["CABELOS", "0.1234", "GIFTS"],
        "receita_aprovada": [100.0, -10.0, 200.0],
        "nr_pedidos": [2, 1, 4],
        "qt_material": [4, 1, 5],
        "vlr_venda_desconto": [20.0, 5.0, 50.0],
    })


def test_prepare_case_data_identifica_categoria_invalida():
    df = prepare_case_data(_sample())

    assert df["categoria_invalida"].tolist() == [False, True, False]
    assert pd.isna(df.loc[1, "categoria_material_limpa"])
    assert bool(df.loc[1, "receita_negativa"])


def test_aggregate_daily_preserva_totais():
    df = prepare_case_data(_sample())
    daily = aggregate_daily(df)

    first = daily.iloc[0]
    assert first["receita_aprovada"] == 90.0
    assert first["nr_pedidos"] == 3
    assert first["qt_material"] == 5


def test_weekday_summary_cria_indice_potencial():
    df = prepare_case_data(_sample())
    daily = aggregate_daily(df)
    report = weekday_summary(daily)

    assert "indice_potencial_itens" in report.columns


def test_quality_summary_sinaliza_categoria_invalida_e_receita_negativa():
    df = prepare_case_data(_sample())
    report = quality_summary(df).set_index("check")

    assert report.loc["categorias_invalidas", "status"] == "REVISAR"
    assert report.loc["receita_negativa", "status"] == "REVISAR"
