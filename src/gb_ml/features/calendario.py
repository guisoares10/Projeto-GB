"""Calendário comercial: datas comemorativas e campanhas usadas como features.

As datas comemorativas e a Black November são calculadas por regra, para
qualquer ano. Assim, quando a próxima Black Friday chegar, as flags já existem
sem precisar de ajuste. As demais campanhas não seguem regra fixa: são
informadas pelo negócio (premissa).
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

# Janela da flag: o próprio dia do evento e os DIAS_ANTES dias anteriores
DIAS_ANTES = 7
# Distância até a próxima / desde a última data comemorativa, limitada (acima disso = "longe de qualquer data")
LIMITE_DISTANCIA = 15
COLUNAS_DISTANCIA = ["dias_ate_evento", "dias_desde_evento"]

# Campanhas pontuais informadas pelo negócio (premissa): nome, início, fim (inclusive).
# A Black November não entra aqui: tem coluna própria, calculada por regra.
CAMPANHAS = [
    ("campanha_maio", "2026-05-15", "2026-05-24"),
]


def _n_esimo_dia_semana(ano: int, mes: int, dia_semana: int, n: int) -> dt.date:
    """n-ésima ocorrência de um dia da semana no mês (segunda=0 ... domingo=6)."""
    primeiro = dt.date(ano, mes, 1)
    deslocamento = (dia_semana - primeiro.weekday()) % 7
    return primeiro + dt.timedelta(days=deslocamento + 7 * (n - 1))


def datas_eventos(ano: int) -> dict[str, dt.date]:
    """Datas comemorativas de um ano."""
    return {
        "ano_novo": dt.date(ano, 1, 1),
        "dia_consumidor": dt.date(ano, 3, 15),
        # segundo domingo de maio
        "dia_maes": _n_esimo_dia_semana(ano, 5, 6, 2),
        "dia_namorados": dt.date(ano, 6, 12),
        # sexta-feira seguinte ao Thanksgiving (quarta quinta-feira de novembro)
        "black_friday": _n_esimo_dia_semana(ano, 11, 3, 4) + dt.timedelta(days=1),
        "natal": dt.date(ano, 12, 25),
    }


EVENTOS = list(datas_eventos(2000))


def periodo_black_november(ano: int) -> tuple[dt.date, dt.date]:
    """Black November: da primeira segunda-feira de novembro ao domingo após a Black Friday."""
    inicio = _n_esimo_dia_semana(ano, 11, 0, 1)
    fim = datas_eventos(ano)["black_friday"] + dt.timedelta(days=2)
    return inicio, fim


def tabela_eventos(anos: list[int], dias_antes: int = DIAS_ANTES) -> pd.DataFrame:
    """Uma linha por evento e ano, com a janela em que a flag fica ligada."""
    linhas = []
    for ano in anos:
        for evento, data in datas_eventos(ano).items():
            linhas.append(
                {
                    "evento": evento,
                    "data": pd.Timestamp(data),
                    "inicio_flag": pd.Timestamp(data - dt.timedelta(days=dias_antes)),
                    "fim_flag": pd.Timestamp(data),
                }
            )
    return pd.DataFrame(linhas)


def features_calendario(datas: pd.Series, dias_antes: int = DIAS_ANTES) -> pd.DataFrame:
    """Features de calendário para cada data (mesmo índice da série recebida).

    - dia_semana (segunda=0) e dia_mes;
    - evento_<nome>: 1 entre (data - dias_antes) e a data do evento;
    - black_november: 1 no período de periodo_black_november;
    - campanha: 1 dentro de qualquer período de CAMPANHAS;
    - dias_ate_evento / dias_desde_evento: dias até a próxima e desde a última data
      comemorativa (qualquer uma), de 0 a LIMITE_DISTANCIA. Ensinam o formato da
      venda em torno das datas: cresce conforme a data se aproxima e cai logo depois.
    """
    datas = pd.to_datetime(datas)
    saida = pd.DataFrame(index=datas.index)
    saida["dia_semana"] = datas.dt.dayofweek
    saida["dia_mes"] = datas.dt.day

    anos = sorted(set(datas.dt.year) | {a + 1 for a in datas.dt.year})
    eventos = tabela_eventos(anos, dias_antes)
    for evento in EVENTOS:
        flag = pd.Series(0, index=datas.index)
        for _, linha in eventos[eventos["evento"] == evento].iterrows():
            flag |= datas.between(linha["inicio_flag"], linha["fim_flag"]).astype(int)
        saida[f"evento_{evento}"] = flag

    black_november = pd.Series(0, index=datas.index)
    for ano in anos:
        inicio, fim = periodo_black_november(ano)
        black_november |= datas.between(pd.Timestamp(inicio), pd.Timestamp(fim)).astype(int)
    saida["black_november"] = black_november

    campanha = pd.Series(0, index=datas.index)
    for _, inicio, fim in CAMPANHAS:
        campanha |= datas.between(pd.Timestamp(inicio), pd.Timestamp(fim)).astype(int)
    saida["campanha"] = campanha

    # anos vizinhos para achar a data anterior e a próxima nas pontas da série
    datas_evento = np.sort(pd.to_datetime(
        tabela_eventos([anos[0] - 1, *anos], dias_antes)["data"]).values)
    valores = datas.values
    proxima = np.searchsorted(datas_evento, valores, side="left")
    anterior = np.searchsorted(datas_evento, valores, side="right") - 1
    um_dia = np.timedelta64(1, "D")
    saida["dias_ate_evento"] = np.minimum((datas_evento[proxima] - valores) / um_dia, LIMITE_DISTANCIA).astype(int)
    saida["dias_desde_evento"] = np.minimum((valores - datas_evento[anterior]) / um_dia, LIMITE_DISTANCIA).astype(int)
    return saida
