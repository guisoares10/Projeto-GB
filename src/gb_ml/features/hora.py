"""Features da previsão por hora (grão hora × canal × categoria)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .calendario import features_calendario
from .vendas import ALVO, CHAVE, HORIZONTE, _dummies, matriz_arvore, matriz_linear

# Lags do mesmo horário e mesmo dia da semana. Com previsão 14 dias à frente,
# a semana mais recente disponível é a de 2 semanas antes.
SEMANAS_LAG_HORA = [2, 3, 4]
COLUNAS_LAG_HORA = [f"lag_{s}sem_mesma_hora" for s in SEMANAS_LAG_HORA] + ["media_2a4sem_mesma_hora"]


def montar_features_hora(base: pd.DataFrame, horizonte: int = HORIZONTE) -> pd.DataFrame:
    """Calendário, eventos, canal, hora do dia e lags do mesmo horário.

    Espera uma linha por hora × canal × categoria, sem buracos de horas
    (a query horária completa a grade com zero).
    """
    if 7 * min(SEMANAS_LAG_HORA) < horizonte:
        raise ValueError("lags do mesmo horário menores que o horizonte de previsão")

    df = base.copy()
    df["hora"] = pd.to_datetime(df["hora"])
    df["data"] = pd.to_datetime(df["data"])
    df = df.sort_values([*CHAVE, "hora"]).reset_index(drop=True)

    horas = df.groupby(CHAVE)["hora"].agg(["min", "max", "count"])
    esperado = (horas["max"] - horas["min"]) / pd.Timedelta(hours=1) + 1
    if (horas["count"] != esperado).any():
        raise ValueError("há buracos de horas em alguma série; complete a grade antes")

    df = pd.concat([df, features_calendario(df["data"])], axis=1)
    df["is_app"] = (df["des_canal_venda_final_agrup"] == "App").astype(int)
    df["hora_dia"] = df["hora"].dt.hour

    serie = df.groupby(CHAVE)[ALVO]
    for semanas in SEMANAS_LAG_HORA:
        df[f"lag_{semanas}sem_mesma_hora"] = serie.shift(24 * 7 * semanas)
    lags = [f"lag_{s}sem_mesma_hora" for s in SEMANAS_LAG_HORA]
    df["media_2a4sem_mesma_hora"] = df[lags].mean(axis=1, skipna=False)
    return df


def matriz_linear_hora(df: pd.DataFrame, interacao: bool = False, usar_lags: bool = False) -> pd.DataFrame:
    """Matriz da regressão linear diária mais dummies de hora do dia (referência: 0h)."""
    partes = [
        matriz_linear(df, interacao),
        _dummies(df, "hora_dia", "hora", remover_primeira=True),
    ]
    if usar_lags:
        partes.append(np.log1p(df[COLUNAS_LAG_HORA]))
    return pd.concat(partes, axis=1).astype(float)


def matriz_arvore_hora(df: pd.DataFrame, usar_lags: bool = True) -> pd.DataFrame:
    """Matriz das árvores diária mais hora do dia e (opcional) lags do mesmo horário."""
    partes = [matriz_arvore(df, usar_lags=False), df[["hora_dia"]]]
    if usar_lags:
        partes.append(df[COLUNAS_LAG_HORA])
    return pd.concat(partes, axis=1).astype(float)


def distribuir_por_hora(
    previsao_dia: pd.DataFrame,
    base_hora: pd.DataFrame,
    folds: pd.DataFrame,
    chave: list[str] | None = None,
    dias_perfil: int = 28,
) -> pd.DataFrame:
    """Reparte uma previsão diária pelas horas do dia.

    O perfil é a participação de cada hora no volume da série, por dia da
    semana, nos `dias_perfil` dias anteriores a cada rodada (só passado).
    `chave` define o nível do perfil: série (canal × categoria) ou [] para o total.
    """
    chave = CHAVE if chave is None else chave
    base_hora = base_hora.assign(dia_semana=base_hora["data"].dt.dayofweek, hora_dia=base_hora["hora"].dt.hour)
    if not chave:
        base_hora = base_hora.groupby(["hora", "data", "dia_semana", "hora_dia"], as_index=False)[ALVO].sum()
    saidas = []
    for _, fold in folds.iterrows():
        passado = base_hora[
            (base_hora["data"] < fold["inicio"])
            & (base_hora["data"] >= fold["inicio"] - pd.Timedelta(days=dias_perfil))
        ]
        perfil = (
            passado.groupby([*chave, "dia_semana", "hora_dia"])[ALVO].sum()
            / passado.groupby([*chave, "dia_semana"])[ALVO].sum()
        ).rename("perfil").reset_index()
        teste = base_hora[base_hora["data"].between(fold["inicio"], fold["fim"])]
        teste = teste[["hora", "data", "dia_semana", "hora_dia", *chave, ALVO]]
        dia = previsao_dia[previsao_dia["rodada"] == fold["rodada"]]
        dia = dia.groupby(["data", *chave], as_index=False)["previsto"].sum().rename(columns={"previsto": "previsto_dia"})
        teste = teste.merge(dia, on=["data", *chave]).merge(perfil, on=[*chave, "dia_semana", "hora_dia"], how="left")
        saidas.append(teste.assign(rodada=fold["rodada"], previsto=teste["previsto_dia"] * teste["perfil"].fillna(0)))
    return pd.concat(saidas, ignore_index=True)
