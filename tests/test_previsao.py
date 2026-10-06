import datetime as dt

import numpy as np
import pandas as pd
import pytest

from gb_ml.features import datas_eventos, features_calendario, montar_features
from gb_ml.model import baseline, gerar_folds, metricas, rodar_backtest


def base_sintetica(dias: int = 60) -> pd.DataFrame:
    datas = pd.date_range("2026-01-01", periods=dias, freq="D")
    linhas = []
    for canal in ["App", "Site"]:
        for categoria in ["A", "B"]:
            for i, data in enumerate(datas):
                linhas.append(
                    {
                        "data": data,
                        "des_canal_venda_final_agrup": canal,
                        "des_categoria_material": categoria,
                        "qt_material": float(i + (100 if canal == "App" else 0)),
                        "taxa_desconto_dia": 0.3,
                    }
                )
    return pd.DataFrame(linhas)


def test_datas_eventos_por_regra():
    assert datas_eventos(2025)["black_friday"] == dt.date(2025, 11, 28)
    assert datas_eventos(2026)["black_friday"] == dt.date(2026, 11, 27)
    assert datas_eventos(2026)["dia_maes"] == dt.date(2026, 5, 10)
    assert datas_eventos(2027)["dia_maes"] == dt.date(2027, 5, 9)


def test_flag_cobre_semana_anterior_e_o_dia():
    datas = pd.Series(pd.to_datetime(["2026-05-02", "2026-05-03", "2026-05-10", "2026-05-11"]))
    flags = features_calendario(datas)
    assert flags["evento_dia_maes"].tolist() == [0, 1, 1, 0]


def test_ano_novo_usa_o_ano_seguinte():
    flags = features_calendario(pd.Series(pd.to_datetime(["2025-12-24", "2025-12-26"])))
    assert flags["evento_ano_novo"].tolist() == [0, 1]


def test_campanha_black_november():
    flags = features_calendario(pd.Series(pd.to_datetime(["2025-11-02", "2025-11-03", "2025-12-01"])))
    assert flags["campanha"].tolist() == [0, 1, 0]


def test_lag_usa_o_valor_de_14_dias_antes():
    df = montar_features(base_sintetica())
    serie = df[(df["des_canal_venda_final_agrup"] == "App") & (df["des_categoria_material"] == "A")]
    serie = serie.set_index("data")
    assert serie.loc["2026-01-20", "lag_14"] == serie.loc["2026-01-06", "qt_material"]
    assert np.isnan(serie.loc["2026-01-10", "lag_14"])


def test_buraco_de_data_gera_erro():
    base = base_sintetica()
    with pytest.raises(ValueError):
        montar_features(base[base["data"] != "2026-01-15"])


def test_folds_crescem_e_terminam_no_fim():
    folds = gerar_folds("2026-04-01", "2026-06-30", horizonte=14)
    assert len(folds) == 7
    assert folds["fim"].iloc[-1] == pd.Timestamp("2026-06-30")
    assert (folds["inicio"].diff().dropna() == pd.Timedelta(days=14)).all()


def test_metricas():
    m = metricas([10, 10], [12, 6])
    assert m["wape"] == pytest.approx(0.3)
    assert m["mae"] == pytest.approx(3.0)
    assert m["vies"] == pytest.approx(-0.1)


def test_backtest_nao_ve_o_futuro():
    df = montar_features(base_sintetica())
    folds = gerar_folds("2026-02-01", "2026-03-01", horizonte=14)
    vistos = []

    def espiao(treino, teste):
        vistos.append((treino["data"].max(), teste["data"].min()))
        return np.zeros(len(teste))

    rodar_backtest(df, folds, espiao)
    assert all(fim_treino < inicio_teste for fim_treino, inicio_teste in vistos)


def test_baseline_mm7_usa_ultimos_7_dias():
    df = montar_features(base_sintetica())
    folds = gerar_folds("2026-02-01", "2026-02-14", horizonte=14)
    previsoes = rodar_backtest(df, folds, baseline("mm7"))
    app_a = previsoes[
        (previsoes["des_canal_venda_final_agrup"] == "App") & (previsoes["des_categoria_material"] == "A")
    ]
    # treino até 31/01 (i = 30): média de i = 24..30 -> 27, mais 100 do canal App
    assert app_a["previsto"].unique().tolist() == [127.0]
