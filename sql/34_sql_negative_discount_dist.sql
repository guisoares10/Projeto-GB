-- case projeto GB
-- 34_sql_negative_discount_dist.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 2.4.7 É erro de sinal? E o desconto explica alguma coisa?
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

SELECT
  IF(receita_aprovada < 0, 'NEGATIVA (sinal corrigido)', 'POSITIVA') AS grupo,
  APPROX_QUANTILES(SAFE_DIVIDE(vlr_venda_desconto, ABS(receita_aprovada) + vlr_venda_desconto), 100)[OFFSET(25)] AS taxa_p25,
  APPROX_QUANTILES(SAFE_DIVIDE(vlr_venda_desconto, ABS(receita_aprovada) + vlr_venda_desconto), 100)[OFFSET(50)] AS taxa_mediana,
  APPROX_QUANTILES(SAFE_DIVIDE(vlr_venda_desconto, ABS(receita_aprovada) + vlr_venda_desconto), 100)[OFFSET(75)] AS taxa_p75
FROM `{TABLE_ID}`
WHERE {DATE_FILTER}
  AND receita_aprovada != 0
GROUP BY 1
