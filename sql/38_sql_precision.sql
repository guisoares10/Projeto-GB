-- 38_sql_precision.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 2.6 Precisão monetária no BigQuery
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

SELECT
  COUNT(*) AS linhas,
  COUNTIF(receita_aprovada != ROUND(receita_aprovada, 2)) AS receita_aprovada_acima_2_casas,
  COUNTIF(vlr_venda_desconto != ROUND(vlr_venda_desconto, 2)) AS desconto_acima_2_casas
FROM `{TABLE_ID}`
WHERE {DATE_FILTER}
