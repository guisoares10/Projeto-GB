"""Features da previsão diária de qt_material (grão dia × canal × categoria)."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from .calendario import COLUNAS_DISTANCIA, EVENTOS, features_calendario

CHAVE = ["des_canal_venda_final_agrup", "des_categoria_material"]
ALVO = "qt_material"

# Horizonte de previsão: todo lag precisa ser >= HORIZONTE, senão usaria dado
# que ainda não existe no momento da previsão.
HORIZONTE = 14
LAGS = [14, 21, 28]
JANELAS_MEDIA = [7, 28]

COLUNAS_EVENTO = [f"evento_{e}" for e in EVENTOS] + ["black_november", "campanha"]
# Premissa: taxa média de desconto da semana por canal × categoria, informada pelo time de desconto
COLUNA_DESCONTO = "taxa_desconto_semana_canal_categoria"
# Versão anterior (só por categoria), ainda usada pela base horária (44_sql_base_modelagem_hora.sql)
COLUNA_DESCONTO_CATEGORIA = "taxa_desconto_semana_categoria"
# No modelo geral (sem categoria) a premissa é a taxa média da semana do total
COLUNA_DESCONTO_GERAL = "taxa_desconto_semana"
COLUNAS_LAG = [f"lag_{l}" for l in LAGS] + [f"mm{j}_lag{HORIZONTE}" for j in JANELAS_MEDIA]


def montar_features(base: pd.DataFrame, horizonte: int = HORIZONTE) -> pd.DataFrame:
    """Acrescenta calendário, eventos, canal e lags à base de modelagem.

    Espera uma linha por data × canal × categoria, sem buracos de datas
    (a query de modelagem completa a grade com zero).
    """
    if min(LAGS) < horizonte:
        raise ValueError(f"lags {LAGS} menores que o horizonte de {horizonte} dias")

    df = base.copy()
    df["data"] = pd.to_datetime(df["data"])
    df = df.sort_values([*CHAVE, "data"]).reset_index(drop=True)

    dias = df.groupby(CHAVE)["data"].agg(["min", "max", "count"])
    esperado = (dias["max"] - dias["min"]).dt.days + 1
    if (dias["count"] != esperado).any():
        raise ValueError("há buracos de datas em alguma série; complete a grade antes")

    df = pd.concat([df, features_calendario(df["data"])], axis=1)
    df["is_app"] = (df["des_canal_venda_final_agrup"] == "App").astype(int)

    serie = df.groupby(CHAVE)[ALVO]
    for lag in LAGS:
        df[f"lag_{lag}"] = serie.shift(lag)
    for janela in JANELAS_MEDIA:
        df[f"mm{janela}_lag{horizonte}"] = serie.transform(
            lambda s, j=janela: s.shift(horizonte).rolling(j).mean()
        )
    return df


def _dummies(df: pd.DataFrame, coluna: str, prefixo: str, remover_primeira: bool) -> pd.DataFrame:
    categorias = sorted(df[coluna].unique())
    valores = pd.Categorical(df[coluna], categories=categorias)
    dummies = pd.get_dummies(valores, prefix=prefixo, drop_first=remover_primeira, dtype=int)
    # nomes só com letras, números e "_" (LightGBM e XGBoost recusam alguns símbolos)
    dummies.columns = [re.sub(r"\W+", "_", str(c)).strip("_").lower() for c in dummies.columns]
    return dummies.set_index(df.index)


def colunas_desconto(df: pd.DataFrame) -> list[str]:
    """Coluna de desconto presente na base (por categoria ou do total)."""
    return [c for c in (COLUNA_DESCONTO, COLUNA_DESCONTO_CATEGORIA, COLUNA_DESCONTO_GERAL) if c in df.columns]


def matriz_linear(df: pd.DataFrame, interacao: bool = False, usar_lags: bool = False) -> pd.DataFrame:
    """Matriz da regressão linear: tudo em dummies, com uma categoria de referência.

    Referências: segunda-feira, canal Site e a primeira categoria em ordem alfabética.
    Com `usar_lags`, entram os lags em log(1 + valor), na mesma escala do alvo em log.
    """
    partes = [
        df[["is_app", *colunas_desconto(df), *COLUNAS_EVENTO]],
        _dummies(df, "dia_semana", "dia_semana", remover_primeira=True),
        _dummies(df, "des_categoria_material", "cat", remover_primeira=True),
    ]
    if interacao:
        cat = _dummies(df, "des_categoria_material", "app_x_cat", remover_primeira=True)
        partes.append(cat.mul(df["is_app"], axis=0))
    if usar_lags:
        partes.append(np.log1p(df[COLUNAS_LAG]))
    return pd.concat(partes, axis=1).astype(float)


def matriz_arvore(df: pd.DataFrame, usar_lags: bool = True) -> pd.DataFrame:
    """Matriz das árvores: dummies de categoria, calendário numérico, distância às datas e (opcional) lags."""
    partes = [
        df[["is_app", "dia_semana", "dia_mes", *colunas_desconto(df), *COLUNAS_EVENTO, *COLUNAS_DISTANCIA]],
        _dummies(df, "des_categoria_material", "cat", remover_primeira=False),
    ]
    if usar_lags:
        partes.append(df[COLUNAS_LAG])
    return pd.concat(partes, axis=1).astype(float)


def base_geral(base: pd.DataFrame) -> pd.DataFrame:
    """Soma a base dia × canal × categoria no total do dia (uma série só).

    Canal e categoria viram "TOTAL", para que backtest e métricas funcionem sem
    mudança. A premissa de desconto passa a ser a taxa média da semana do total
    (segunda a domingo): desconto ÷ (receita + desconto).
    """
    total = (
        base.assign(data=pd.to_datetime(base["data"]))
        .groupby("data", as_index=False)[[ALVO, "receita_aprovada", "vlr_venda_desconto"]]
        .sum()
    )
    semana = total.groupby(total["data"].dt.to_period("W-SUN"))
    desconto = semana["vlr_venda_desconto"].transform("sum")
    total[COLUNA_DESCONTO_GERAL] = desconto / (semana["receita_aprovada"].transform("sum") + desconto)
    return total.assign(**{coluna: "TOTAL" for coluna in CHAVE})
