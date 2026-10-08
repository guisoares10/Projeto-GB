-- 05_sql_price_hypotheses.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: A `receita_aprovada` já vem com o desconto aplicado?
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

SELECT
  des_categoria_material,
  SAFE_DIVIDE(SUM(receita_aprovada), SUM(qt_material)) AS a_pago_por_item,
  SAFE_DIVIDE(SUM(receita_aprovada + vlr_venda_desconto), SUM(qt_material)) AS a_preco_cheio_por_item,
  SAFE_DIVIDE(SUM(receita_aprovada - vlr_venda_desconto), SUM(qt_material)) AS b_pago_por_item,
  SAFE_DIVIDE(SUM(receita_aprovada), SUM(qt_material)) AS b_preco_cheio_por_item
FROM `{TABLE_ID}`
WHERE {DATE_FILTER}
  AND receita_aprovada >= 0
  AND SAFE_CAST(des_categoria_material AS NUMERIC) IS NULL
GROUP BY 1
ORDER BY a_pago_por_item
