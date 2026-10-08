-- case projeto GB
-- 07_sql_discount_overview.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: Números gerais do desconto
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

SELECT
  CASE
    WHEN vlr_venda_desconto > 0 THEN 'COM_DESCONTO'
    WHEN vlr_venda_desconto = 0 THEN 'SEM_DESCONTO'
    WHEN vlr_venda_desconto < 0 THEN 'DESCONTO_NEGATIVO'
    ELSE 'NULO'
  END AS grupo_desconto,
  COUNT(*) AS linhas,
  SUM(nr_pedidos) AS nr_pedidos,
  SUM(qt_material) AS qt_material,
  CAST(SUM(receita_aprovada) AS FLOAT64) AS receita_aprovada,
  CAST(SUM(vlr_venda_desconto) AS FLOAT64) AS vlr_venda_desconto
FROM `{TABLE_ID}`
WHERE {DATE_FILTER}
GROUP BY 1
ORDER BY linhas DESC
