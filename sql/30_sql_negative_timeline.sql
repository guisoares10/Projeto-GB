-- case projeto GB
-- 30_sql_negative_timeline.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 2.4.4 Quando a receita negativa aparece na linha do tempo?
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

SELECT
  DATE(dt_hr_venda) AS data,
  COUNTIF(receita_aprovada < 0) AS linhas_negativas,
  CAST(
    -SUM(IF(receita_aprovada < 0, receita_aprovada, 0))
    AS FLOAT64
  ) AS valor_negativo_abs,
  CAST(SUM(receita_aprovada) AS FLOAT64) AS receita_aprovada_liquida_dia
FROM `{TABLE_ID}`
WHERE {DATE_FILTER}
GROUP BY 1
ORDER BY 1
