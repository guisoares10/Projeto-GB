-- 39_sql_precision_impact.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 2.6.1 Impacto financeiro da normalização para 2 casas
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, STG_TABLE_ID

WITH base AS (
  SELECT
    SAFE_CAST(receita_aprovada AS BIGNUMERIC) AS receita_aprovada_original
  FROM `{STG_TABLE_ID}`
  WHERE {DATE_FILTER}
    AND receita_aprovada IS NOT NULL
),
calc AS (
  SELECT
    receita_aprovada_original,
    ROUND(receita_aprovada_original, 2) AS receita_aprovada_round_2,
    TRUNC(receita_aprovada_original, 2) AS receita_aprovada_trunc_2
  FROM base
)
SELECT
  CAST(SUM(receita_aprovada_original) AS FLOAT64) AS receita_aprovada_original_total,
  CAST(SUM(receita_aprovada_round_2) AS FLOAT64) AS receita_aprovada_round_2_total,
  CAST(SUM(receita_aprovada_trunc_2) AS FLOAT64) AS receita_aprovada_trunc_2_total,

  CAST(SUM(receita_aprovada_original - receita_aprovada_round_2) AS FLOAT64)
    AS diferenca_liquida_round,

  CAST(SUM(ABS(receita_aprovada_original - receita_aprovada_round_2)) AS FLOAT64)
    AS ajuste_absoluto_total_round,

  CAST(MAX(ABS(receita_aprovada_original - receita_aprovada_round_2)) AS FLOAT64)
    AS maior_ajuste_linha_round,

  SAFE_DIVIDE(
    CAST(ABS(SUM(receita_aprovada_original - receita_aprovada_round_2)) AS FLOAT64),
    CAST(ABS(SUM(receita_aprovada_original)) AS FLOAT64)
  ) AS pct_impacto_liquido_round,

  CAST(SUM(receita_aprovada_original - receita_aprovada_trunc_2) AS FLOAT64)
    AS diferenca_liquida_trunc,

  CAST(SUM(ABS(receita_aprovada_original - receita_aprovada_trunc_2)) AS FLOAT64)
    AS ajuste_absoluto_total_trunc,

  SAFE_DIVIDE(
    CAST(ABS(SUM(receita_aprovada_original - receita_aprovada_trunc_2)) AS FLOAT64),
    CAST(ABS(SUM(receita_aprovada_original)) AS FLOAT64)
  ) AS pct_impacto_liquido_trunc

FROM calc
