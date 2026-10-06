-- 27_sql_negative_by_channel.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 2.4.1 Existe padrão por canal?
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

SELECT
  des_canal_venda_final_agrup,
  COUNT(*) AS linhas,
  COUNTIF(receita_aprovada < 0) AS linhas_negativas,
  SAFE_DIVIDE(
    COUNTIF(receita_aprovada < 0),
    COUNT(*)
  ) AS pct_linhas_negativas,

  CAST(SUM(IF(receita_aprovada < 0, receita_aprovada, 0)) AS FLOAT64)
    AS receita_aprovada_negativa,

  CAST(SUM(IF(receita_aprovada >= 0, receita_aprovada, 0)) AS FLOAT64)
    AS receita_aprovada_positiva,

  SAFE_DIVIDE(
    -CAST(SUM(IF(receita_aprovada < 0, receita_aprovada, 0)) AS FLOAT64),
    CAST(SUM(IF(receita_aprovada >= 0, receita_aprovada, 0)) AS FLOAT64)
  ) AS impacto_negativo_sobre_positivo

FROM `{TABLE_ID}`
WHERE {DATE_FILTER}
GROUP BY 1
ORDER BY ABS(receita_aprovada_negativa) DESC
