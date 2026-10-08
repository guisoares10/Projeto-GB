-- case projeto GB
-- 31_sql_negative_revenue_monthly_ratio.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 2.4.5 Receita negativa ao longo dos meses — normalizada pela receita
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

SELECT
  DATE_TRUNC(DATE(dt_hr_venda), MONTH) AS mes,

  CAST(
    SUM(IF(receita_aprovada > 0, receita_aprovada, 0))
    AS FLOAT64
  ) AS receita_aprovada_positiva,

  CAST(
    -SUM(IF(receita_aprovada < 0, receita_aprovada, 0))
    AS FLOAT64
  ) AS receita_aprovada_negativa_abs,

  CAST(
    SUM(receita_aprovada)
    AS FLOAT64
  ) AS receita_aprovada_liquida,

  COUNT(*) AS linhas,

  COUNTIF(receita_aprovada < 0)
    AS linhas_receita_aprovada_negativa,

  SAFE_DIVIDE(
    COUNTIF(receita_aprovada < 0),
    COUNT(*)
  ) AS pct_linhas_receita_aprovada_negativa,

  SAFE_DIVIDE(
    -CAST(
      SUM(IF(receita_aprovada < 0, receita_aprovada, 0))
      AS FLOAT64
    ),
    CAST(
      SUM(IF(receita_aprovada > 0, receita_aprovada, 0))
      AS FLOAT64
    )
  ) AS impacto_negativo_pct_receita_aprovada_positiva

FROM `{TABLE_ID}`
WHERE {DATE_FILTER}
GROUP BY 1
ORDER BY 1
