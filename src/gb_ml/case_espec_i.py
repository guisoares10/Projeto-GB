"""Preparação específica do Case Técnico | Especialista de Dados I."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

EXPECTED_COLUMNS = [
    "dt_hr_venda",
    "des_canal_venda_final_agrup",
    "des_categoria_material",
    "receita_aprovada",
    "nr_pedidos",
    "qt_material",
    "vlr_venda_desconto",
]

VALID_CHANNELS = {"App", "Site"}

WEEKDAY_PT = {
    0: "Segunda",
    1: "Terça",
    2: "Quarta",
    3: "Quinta",
    4: "Sexta",
    5: "Sábado",
    6: "Domingo",
}


def load_case_csv(path: str | Path) -> pd.DataFrame:
    """Carrega e valida o arquivo entregue no case."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {path}. "
            "Coloque 'Dados - Case Técnico Espec I.csv' dentro da pasta data/."
        )

    df = pd.read_csv(path)
    df.columns = [str(column).strip().lower() for column in df.columns]
    missing = [column for column in EXPECTED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes no CSV: {missing}")
    return df



def load_case_bigquery(
    table_id: str = "gms-prod-01.projeto_gb.fact_vendas",
    *,
    project_id: str = "gms-prod-01",
    location: str = "us-east4",
) -> pd.DataFrame:
    """Carrega a fact curada diretamente do BigQuery."""
    from gb_ml.io import read_query

    sql = f"SELECT * FROM `{table_id}` ORDER BY dt_hr_venda"
    df = read_query(
        sql,
        project_id=project_id,
        location=location,
    )
    df.columns = [str(column).strip().lower() for column in df.columns]

    missing = [column for column in EXPECTED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes no BigQuery: {missing}")
    return df

def prepare_case_data(df: pd.DataFrame) -> pd.DataFrame:
    """Tipa campos, cria flags de qualidade e features temporais do case."""
    work = df.copy()

    work["dt_hr_venda"] = pd.to_datetime(work["dt_hr_venda"], errors="coerce")
    if work["dt_hr_venda"].isna().any():
        raise ValueError(
            f"Existem {int(work['dt_hr_venda'].isna().sum())} timestamps inválidos."
        )

    for column in [
        "receita_aprovada",
        "nr_pedidos",
        "qt_material",
        "vlr_venda_desconto",
    ]:
        work[column] = pd.to_numeric(work[column], errors="coerce")

    category_numeric = pd.to_numeric(
        work["des_categoria_material"].astype(str),
        errors="coerce",
    )
    work["categoria_invalida"] = category_numeric.notna()
    work["categoria_material_limpa"] = work["des_categoria_material"].where(
        ~work["categoria_invalida"],
        pd.NA,
    )

    work["receita_negativa"] = work["receita_aprovada"] < 0
    work["receita_zero"] = work["receita_aprovada"] == 0

    work["data"] = work["dt_hr_venda"].dt.normalize()
    work["hora"] = work["dt_hr_venda"].dt.hour
    work["dia_semana_num"] = work["dt_hr_venda"].dt.dayofweek
    work["dia_semana"] = work["dia_semana_num"].map(WEEKDAY_PT)
    work["mes"] = work["dt_hr_venda"].dt.to_period("M").astype(str)
    work["semana_ano"] = work["dt_hr_venda"].dt.isocalendar().week.astype(int)
    work["fim_de_semana"] = work["dia_semana_num"].isin([5, 6]).astype(int)

    work["preco_medio_item_linha"] = (
        work["receita_aprovada"] / work["qt_material"].replace(0, np.nan)
    )
    work["ticket_medio_linha"] = (
        work["receita_aprovada"] / work["nr_pedidos"].replace(0, np.nan)
    )
    work["itens_por_pedido_linha"] = (
        work["qt_material"] / work["nr_pedidos"].replace(0, np.nan)
    )

    gross = work["receita_aprovada"] + work["vlr_venda_desconto"]
    work["taxa_desconto_linha"] = np.where(
        gross > 0,
        work["vlr_venda_desconto"] / gross,
        np.nan,
    )

    return work


def valid_categories(df: pd.DataFrame) -> list[str]:
    """Retorna as categorias textuais válidas identificadas no arquivo."""
    values = (
        df.loc[~df["categoria_invalida"], "des_categoria_material"]
        .dropna()
        .astype(str)
        .unique()
    )
    return sorted(values.tolist())


def quality_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Consolida os principais checks de qualidade específicos do case."""
    grain = [
        "dt_hr_venda",
        "des_canal_venda_final_agrup",
        "des_categoria_material",
    ]

    expected_start = pd.Timestamp("2025-11-01 00:00:00")
    expected_end = pd.Timestamp("2026-06-30 23:00:00")

    expected_hours = pd.date_range(
        df["dt_hr_venda"].min(),
        df["dt_hr_venda"].max(),
        freq="h",
    )
    present_hours = pd.DatetimeIndex(df["dt_hr_venda"].unique())
    missing_hours = expected_hours.difference(present_hours)

    records = [
        {
            "check": "schema_colunas",
            "status": "OK" if all(c in df.columns for c in EXPECTED_COLUMNS) else "ERRO",
            "valor": len([c for c in EXPECTED_COLUMNS if c in df.columns]),
            "esperado": len(EXPECTED_COLUMNS),
            "observacao": "Campos descritos no enunciado.",
        },
        {
            "check": "periodo_inicio",
            "status": "OK" if df["dt_hr_venda"].min() == expected_start else "REVISAR",
            "valor": df["dt_hr_venda"].min(),
            "esperado": expected_start,
            "observacao": "Início informado no enunciado.",
        },
        {
            "check": "periodo_fim",
            "status": "OK" if df["dt_hr_venda"].max() == expected_end else "REVISAR",
            "valor": df["dt_hr_venda"].max(),
            "esperado": expected_end,
            "observacao": "Fim informado no enunciado.",
        },
        {
            "check": "timestamps_invalidos",
            "status": "OK" if df["dt_hr_venda"].isna().sum() == 0 else "ERRO",
            "valor": int(df["dt_hr_venda"].isna().sum()),
            "esperado": 0,
            "observacao": "Datas devem ser parseáveis.",
        },
        {
            "check": "nulos_totais",
            "status": "OK" if df[EXPECTED_COLUMNS].isna().sum().sum() == 0 else "REVISAR",
            "valor": int(df[EXPECTED_COLUMNS].isna().sum().sum()),
            "esperado": 0,
            "observacao": "Nulos nas colunas originais.",
        },
        {
            "check": "duplicidade_grao",
            "status": "OK" if df.duplicated(grain).sum() == 0 else "ERRO",
            "valor": int(df.duplicated(grain).sum()),
            "esperado": 0,
            "observacao": "Grão esperado: hora × canal × categoria.",
        },
        {
            "check": "horas_sem_registro",
            "status": "OK" if len(missing_hours) == 0 else "REVISAR",
            "valor": len(missing_hours),
            "esperado": 0,
            "observacao": "Cobertura horária global do período.",
        },
        {
            "check": "categorias_invalidas",
            "status": "REVISAR" if df["categoria_invalida"].any() else "OK",
            "valor": int(df["categoria_invalida"].sum()),
            "esperado": 0,
            "observacao": "Valores numéricos encontrados em campo categórico.",
        },
        {
            "check": "receita_negativa",
            "status": "REVISAR" if df["receita_negativa"].any() else "OK",
            "valor": int(df["receita_negativa"].sum()),
            "esperado": "validar regra de negócio",
            "observacao": "Pode refletir estorno/ajuste; não remover automaticamente.",
        },
        {
            "check": "qt_material_nao_positiva",
            "status": "OK" if (df["qt_material"] <= 0).sum() == 0 else "ERRO",
            "valor": int((df["qt_material"] <= 0).sum()),
            "esperado": 0,
            "observacao": "Quantidade vendida deve ser positiva nas linhas existentes.",
        },
        {
            "check": "nr_pedidos_nao_positivo",
            "status": "OK" if (df["nr_pedidos"] <= 0).sum() == 0 else "ERRO",
            "valor": int((df["nr_pedidos"] <= 0).sum()),
            "esperado": 0,
            "observacao": "Pedidos devem ser positivos nas linhas existentes.",
        },
        {
            "check": "canal_fora_dominio",
            "status": "OK" if set(df["des_canal_venda_final_agrup"].unique()) <= VALID_CHANNELS else "ERRO",
            "valor": sorted(df["des_canal_venda_final_agrup"].unique().tolist()),
            "esperado": sorted(VALID_CHANNELS),
            "observacao": "Domínio informado: App/Site.",
        },
    ]

    return pd.DataFrame(records)


def aggregate_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Cria a série diária que será a base da modelagem."""
    daily = (
        df.groupby("data", as_index=False)
        .agg(
            receita_aprovada=("receita_aprovada", "sum"),
            nr_pedidos=("nr_pedidos", "sum"),
            qt_material=("qt_material", "sum"),
            vlr_venda_desconto=("vlr_venda_desconto", "sum"),
        )
        .sort_values("data")
        .reset_index(drop=True)
    )

    daily["preco_medio_item"] = (
        daily["receita_aprovada"] / daily["qt_material"]
    )
    daily["ticket_medio"] = (
        daily["receita_aprovada"] / daily["nr_pedidos"]
    )
    daily["itens_por_pedido"] = (
        daily["qt_material"] / daily["nr_pedidos"]
    )

    gross = daily["receita_aprovada"] + daily["vlr_venda_desconto"]
    daily["taxa_desconto"] = np.where(
        gross > 0,
        daily["vlr_venda_desconto"] / gross,
        np.nan,
    )

    daily["dia_semana_num"] = daily["data"].dt.dayofweek
    daily["dia_semana"] = daily["dia_semana_num"].map(WEEKDAY_PT)
    daily["mes"] = daily["data"].dt.to_period("M").astype(str)
    daily["fim_de_semana"] = daily["dia_semana_num"].isin([5, 6]).astype(int)

    return daily


def weekday_summary(daily: pd.DataFrame) -> pd.DataFrame:
    """Resume potencial de demanda/venda por dia da semana."""
    result = (
        daily.groupby(["dia_semana_num", "dia_semana"], as_index=False)
        .agg(
            dias=("data", "count"),
            receita_media=("receita_aprovada", "mean"),
            receita_mediana=("receita_aprovada", "median"),
            itens_media=("qt_material", "mean"),
            itens_mediana=("qt_material", "median"),
            pedidos_media=("nr_pedidos", "mean"),
            preco_medio_item=("preco_medio_item", "mean"),
        )
        .sort_values("dia_semana_num")
    )

    overall_median = daily["qt_material"].median()
    result["indice_potencial_itens"] = (
        result["itens_mediana"] / overall_median
    )
    return result


def hourly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Mede flutuação intradiária sem enviesar pela quantidade de linhas."""
    hourly_daily = (
        df.groupby(["data", "hora"], as_index=False)
        .agg(
            receita_aprovada=("receita_aprovada", "sum"),
            nr_pedidos=("nr_pedidos", "sum"),
            qt_material=("qt_material", "sum"),
        )
    )

    totals = hourly_daily.groupby("data")[
        ["receita_aprovada", "nr_pedidos", "qt_material"]
    ].transform("sum")

    hourly_daily["share_receita"] = (
        hourly_daily["receita_aprovada"] / totals["receita_aprovada"]
    )
    hourly_daily["share_pedidos"] = (
        hourly_daily["nr_pedidos"] / totals["nr_pedidos"]
    )
    hourly_daily["share_itens"] = (
        hourly_daily["qt_material"] / totals["qt_material"]
    )

    return (
        hourly_daily.groupby("hora", as_index=False)
        .agg(
            receita_media=("receita_aprovada", "mean"),
            receita_mediana=("receita_aprovada", "median"),
            itens_media=("qt_material", "mean"),
            pedidos_media=("nr_pedidos", "mean"),
            share_receita_media=("share_receita", "mean"),
            share_itens_media=("share_itens", "mean"),
        )
        .sort_values("hora")
    )
