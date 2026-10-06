"""Validação faseada (janela expansível), métricas e baselines."""

from __future__ import annotations

from itertools import product
from typing import Callable

import numpy as np
import pandas as pd

from gb_ml.features.vendas import ALVO, CHAVE, HORIZONTE

# ajustar_prever(treino, teste) -> previsões de qt_material para as linhas de teste
AjustarPrever = Callable[[pd.DataFrame, pd.DataFrame], np.ndarray]


def gerar_folds(
    inicio_teste: str, fim: str, horizonte: int = HORIZONTE, passo: int | None = None
) -> pd.DataFrame:
    """Rodadas do teste faseado: treino até a véspera, previsão dos próximos `horizonte` dias.

    O treino cresce `passo` dias a cada rodada (padrão: o próprio horizonte).
    A última rodada é cortada em `fim`.
    """
    passo = passo or horizonte
    inicio, fim = pd.Timestamp(inicio_teste), pd.Timestamp(fim)
    rodadas = []
    while inicio <= fim:
        fim_rodada = min(inicio + pd.Timedelta(days=horizonte - 1), fim)
        rodadas.append({"rodada": len(rodadas) + 1, "inicio": inicio, "fim": fim_rodada})
        inicio += pd.Timedelta(days=passo)
    return pd.DataFrame(rodadas)


def metricas(y: pd.Series | np.ndarray, previsto: pd.Series | np.ndarray) -> dict[str, float]:
    """WAPE, MAE e viés (positivo = superestima), todos sobre os totais."""
    y, previsto = np.asarray(y, dtype=float), np.asarray(previsto, dtype=float)
    erro = previsto - y
    return {
        "wape": np.abs(erro).sum() / y.sum(),
        "mae": np.abs(erro).mean(),
        "vies": erro.sum() / y.sum(),
    }


def rodar_backtest(df: pd.DataFrame, folds: pd.DataFrame, ajustar_prever: AjustarPrever) -> pd.DataFrame:
    """Executa todas as rodadas e devolve as previsões linha a linha."""
    saidas = []
    for _, fold in folds.iterrows():
        treino = df[df["data"] < fold["inicio"]]
        teste = df[df["data"].between(fold["inicio"], fold["fim"])]
        previsto = np.clip(np.asarray(ajustar_prever(treino, teste), dtype=float), 0, None)
        saidas.append(
            teste[["data", *CHAVE, ALVO]].assign(rodada=fold["rodada"], previsto=previsto)
        )
    return pd.concat(saidas, ignore_index=True)


def resumo_backtest(previsoes: pd.DataFrame) -> dict[str, float]:
    """Erro geral em dois níveis: série (dia × canal × categoria) e total do dia."""
    total_dia = previsoes.groupby("data")[[ALVO, "previsto"]].sum()
    serie = metricas(previsoes[ALVO], previsoes["previsto"])
    dia = metricas(total_dia[ALVO], total_dia["previsto"])
    return {
        "wape_serie": serie["wape"],
        "wape_dia": dia["wape"],
        "mae_dia": dia["mae"],
        "vies_dia": dia["vies"],
    }


def erro_por_rodada(previsoes: pd.DataFrame) -> pd.DataFrame:
    """Métricas do total diário em cada rodada."""
    linhas = []
    for rodada, grupo in previsoes.groupby("rodada"):
        total_dia = grupo.groupby("data")[[ALVO, "previsto"]].sum()
        linhas.append(
            {
                "rodada": rodada,
                "inicio": grupo["data"].min(),
                "fim": grupo["data"].max(),
                **metricas(total_dia[ALVO], total_dia["previsto"]),
            }
        )
    return pd.DataFrame(linhas)


def buscar_parametros(
    df: pd.DataFrame,
    folds: pd.DataFrame,
    fabrica: Callable[..., AjustarPrever],
    grade: dict[str, list],
) -> pd.DataFrame:
    """Testa todas as combinações da grade no backtest e ordena pelo WAPE da série."""
    nomes = list(grade)
    resultados = []
    for valores in product(*grade.values()):
        parametros = dict(zip(nomes, valores))
        previsoes = rodar_backtest(df, folds, fabrica(**parametros))
        resultados.append({**parametros, **resumo_backtest(previsoes)})
    return pd.DataFrame(resultados).sort_values("wape_serie").reset_index(drop=True)


def folds_de_ajuste(inicio_rodada: pd.Timestamp, rodadas: int = 3, horizonte: int = HORIZONTE) -> pd.DataFrame:
    """As `rodadas` janelas de `horizonte` dias imediatamente anteriores a `inicio_rodada`."""
    inicio = pd.Timestamp(inicio_rodada) - pd.Timedelta(days=rodadas * horizonte)
    fim = pd.Timestamp(inicio_rodada) - pd.Timedelta(days=1)
    return gerar_folds(str(inicio.date()), str(fim.date()), horizonte)


def backtest_com_ajuste(
    df: pd.DataFrame,
    folds: pd.DataFrame,
    fabrica: Callable[..., AjustarPrever],
    grade: dict[str, list],
    rodadas_ajuste: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Backtest em que cada rodada escolhe os hiperparâmetros só com o próprio passado.

    Antes de prever uma rodada, a grade é testada nas `rodadas_ajuste` janelas
    anteriores a ela (com dados até a véspera). A melhor combinação prevê a rodada.
    Devolve as previsões e os parâmetros escolhidos em cada rodada.
    """
    previsoes, escolhidos = [], []
    for _, fold in folds.iterrows():
        passado = df[df["data"] < fold["inicio"]]
        busca = buscar_parametros(passado, folds_de_ajuste(fold["inicio"], rodadas_ajuste), fabrica, grade)
        parametros = {nome: _python(busca.loc[0, nome]) for nome in grade}
        escolhidos.append({"rodada": fold["rodada"], **parametros, "wape_serie_ajuste": busca.loc[0, "wape_serie"]})
        previsoes.append(rodar_backtest(df, folds[folds["rodada"] == fold["rodada"]], fabrica(**parametros)))
    return pd.concat(previsoes, ignore_index=True), pd.DataFrame(escolhidos)


def _python(valor):
    """Converte escalares numpy (vindos do DataFrame da busca) para tipos Python."""
    return valor.item() if isinstance(valor, np.generic) else valor


def baseline(metodo: str) -> AjustarPrever:
    """Baselines por série, usando só o histórico anterior à rodada.

    - "naive_sazonal": repete a última semana observada (mesmo dia da semana);
    - "mm7" / "mm28": média dos últimos 7 / 28 dias, constante no horizonte.
    """
    if metodo not in {"naive_sazonal", "mm7", "mm28"}:
        raise ValueError(f"baseline desconhecido: {metodo}")

    def ajustar_prever(treino: pd.DataFrame, teste: pd.DataFrame) -> np.ndarray:
        fim_treino = treino["data"].max()
        if metodo == "naive_sazonal":
            ultima_semana = treino[treino["data"] > fim_treino - pd.Timedelta(days=7)]
            ref = ultima_semana.assign(dia_semana=ultima_semana["data"].dt.dayofweek)
            ref = ref.groupby([*CHAVE, "dia_semana"])[ALVO].mean().rename("previsto")
            chaves = teste[CHAVE].assign(dia_semana=teste["data"].dt.dayofweek)
            return chaves.join(ref, on=[*CHAVE, "dia_semana"])["previsto"].fillna(0).to_numpy()
        janela = 7 if metodo == "mm7" else 28
        recente = treino[treino["data"] > fim_treino - pd.Timedelta(days=janela)]
        ref = recente.groupby(CHAVE)[ALVO].mean().rename("previsto")
        return teste[CHAVE].join(ref, on=CHAVE)["previsto"].fillna(0).to_numpy()

    return ajustar_prever
