-- case projeto GB
-- 26_sql_negative_revenue.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 2.4 Receita negativa
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

SELECT
  COUNTIF(receita_aprovada < 0) AS linhas_receita_aprovada_negativa,
  SAFE_DIVIDE(COUNTIF(receita_aprovada < 0), COUNT(*)) AS pct_linhas_negativas,
  CAST(SUM(IF(receita_aprovada < 0, receita_aprovada, 0)) AS FLOAT64) AS receita_aprovada_negativa_total,
  CAST(SUM(IF(receita_aprovada >= 0, receita_aprovada, 0)) AS FLOAT64) AS receita_aprovada_nao_negativa_total,
  SAFE_DIVIDE(
    -CAST(SUM(IF(receita_aprovada < 0, receita_aprovada, 0)) AS FLOAT64),
    CAST(SUM(IF(receita_aprovada >= 0, receita_aprovada, 0)) AS FLOAT64)
  ) AS impacto_abs_negativo_sobre_positivo
FROM `{TABLE_ID}`
WHERE {DATE_FILTER}
