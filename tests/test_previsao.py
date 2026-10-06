import datetime as dt

import numpy as np
import pandas as pd
import pytest

from gb_ml.features import datas_eventos, features_calendario, montar_features
from gb_ml.model import backtest_com_ajuste, baseline, folds_de_ajuste, gerar_folds, metricas, rodar_backtest


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
                        "taxa_desconto_semana_categoria": 0.3,
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


def test_black_november_por_regra():
    datas = pd.Series(pd.to_datetime(["2025-11-02", "2025-11-03", "2025-11-30", "2025-12-01", "2026-11-02", "2026-11-29"]))
    flags = features_calendario(datas)
    assert flags["black_november"].tolist() == [0, 1, 1, 0, 1, 1]
    assert flags["campanha"].sum() == 0


def test_campanha_pontual():
    flags = features_calendario(pd.Series(pd.to_datetime(["2026-05-14", "2026-05-15", "2026-05-24"])))
    assert flags["campanha"].tolist() == [0, 1, 1]


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


def test_folds_de_ajuste_terminam_na_vespera():
    folds = folds_de_ajuste(pd.Timestamp("2026-04-01"), rodadas=3, horizonte=14)
    assert len(folds) == 3
    assert folds["inicio"].iloc[0] == pd.Timestamp("2026-02-18")
    assert folds["fim"].iloc[-1] == pd.Timestamp("2026-03-31")


def test_ajuste_por_rodada_so_usa_o_passado():
    df = montar_features(base_sintetica(90))
    folds = gerar_folds("2026-03-01", "2026-03-31", horizonte=14)
    vistos = []

    def fabrica(fator):
        def ajustar_prever(treino, teste):
            vistos.append((treino["data"].max(), teste["data"].min()))
            return np.full(len(teste), treino["qt_material"].mean() * fator)
        return ajustar_prever

    previsoes, escolhidos = backtest_com_ajuste(df, folds, fabrica, {"fator": [0.5, 1.0]}, rodadas_ajuste=2)
    assert all(fim_treino < inicio_teste for fim_treino, inicio_teste in vistos)
    assert len(escolhidos) == len(folds)
    assert set(previsoes["rodada"]) == set(folds["rodada"])


def test_base_geral_soma_series_e_calcula_desconto_da_semana():
    from gb_ml.features import base_geral

    base = base_sintetica(14).assign(receita_aprovada=70.0, vlr_venda_desconto=30.0)
    geral = base_geral(base)
    assert len(geral) == 14
    assert geral["qt_material"].sum() == base["qt_material"].sum()
    assert geral["taxa_desconto_semana"].round(6).eq(0.3).all()
    assert (geral["des_categoria_material"] == "TOTAL").all()


def base_horaria(dias: int = 35) -> pd.DataFrame:
    horas = pd.date_range("2026-01-05", periods=24 * dias, freq="h")
    linhas = []
    for canal in ["App", "Site"]:
        for i, hora in enumerate(horas):
            linhas.append({
                "hora": hora, "data": hora.normalize(), "des_canal_venda_final_agrup": canal,
                "des_categoria_material": "A", "qt_material": float(i), "taxa_desconto_semana_categoria": 0.3,
            })
    return pd.DataFrame(linhas)


def test_lag_horario_usa_a_mesma_hora_de_2_semanas_antes():
    from gb_ml.features import montar_features_hora

    df = montar_features_hora(base_horaria())
    serie = df[df["des_canal_venda_final_agrup"] == "App"].set_index("hora")
    assert serie.loc["2026-01-19 10:00", "lag_2sem_mesma_hora"] == serie.loc["2026-01-05 10:00", "qt_material"]
    assert np.isnan(serie.loc["2026-01-25 10:00", "lag_3sem_mesma_hora"])


def test_distribuir_por_hora_preserva_o_total_do_dia():
    from gb_ml.features import distribuir_por_hora

    h = base_horaria().assign(qt_material=lambda d: 1.0 + d["hora"].dt.hour)
    folds = gerar_folds("2026-02-02", "2026-02-08", horizonte=7)
    dia = (h[h["data"].between("2026-02-02", "2026-02-08")]
           .groupby(["data", "des_canal_venda_final_agrup", "des_categoria_material"], as_index=False)["qt_material"].sum()
           .assign(previsto=100.0, rodada=1))
    por_hora = distribuir_por_hora(dia, h, folds)
    somado = por_hora.groupby(["data", "des_canal_venda_final_agrup"])["previsto"].sum()
    assert np.allclose(somado, 100.0)


def test_dias_ineditos_pega_so_a_primeira_ocorrencia():
    from gb_ml.model import dias_ineditos

    df = pd.DataFrame({"data": pd.date_range("2026-01-01", periods=40), "evento_x": 0})
    df.loc[df["data"].between("2026-01-05", "2026-01-06"), "evento_x"] = 1
    df.loc[df["data"].between("2026-02-01", "2026-02-02"), "evento_x"] = 1
    folds = gerar_folds("2026-01-03", "2026-02-09", horizonte=14)
    assert list(dias_ineditos(df, folds, ["evento_x"])) == list(pd.to_datetime(["2026-01-05", "2026-01-06"]))
