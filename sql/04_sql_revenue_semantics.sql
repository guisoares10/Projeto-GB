-- case projeto GB
-- 04_sql_revenue_semantics.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: A `receita_aprovada` já vem com o desconto aplicado?
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

SELECT
  COUNTIF(receita_aprovada > 0) AS linhas_receita_positiva,

  -- 1) Em B, desconto > receita significaria venda líquida negativa
  COUNTIF(receita_aprovada > 0 AND vlr_venda_desconto > receita_aprovada) AS linhas_desconto_maior_que_receita,

  -- 2) Linhas com receita zero e desconto positivo: em A é item 100% gratuito (brinde)
  COUNTIF(receita_aprovada = 0) AS linhas_receita_zero,
  COUNTIF(receita_aprovada = 0 AND vlr_venda_desconto > 0) AS linhas_receita_zero_com_desconto,

  -- 3) Taxa de desconto por linha em cada hipótese
  APPROX_QUANTILES(SAFE_DIVIDE(vlr_venda_desconto, receita_aprovada + vlr_venda_desconto), 100)[OFFSET(50)] AS taxa_mediana_hipotese_a,
  MAX(SAFE_DIVIDE(vlr_venda_desconto, receita_aprovada + vlr_venda_desconto)) AS taxa_maxima_hipotese_a,
  APPROX_QUANTILES(IF(receita_aprovada > 0, SAFE_DIVIDE(vlr_venda_desconto, receita_aprovada), NULL), 100)[OFFSET(50)] AS taxa_mediana_hipotese_b,
  APPROX_QUANTILES(IF(receita_aprovada > 0, SAFE_DIVIDE(vlr_venda_desconto, receita_aprovada), NULL), 100)[OFFSET(95)] AS taxa_p95_hipotese_b
FROM `{TABLE_ID}`
WHERE {DATE_FILTER}
  AND receita_aprovada >= 0
