-- case projeto GB
-- 06_sql_free_items.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: A `receita_aprovada` já vem com o desconto aplicado?
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

SELECT
  des_categoria_material,
  qt_material,
  receita_aprovada,
  vlr_venda_desconto,
  SAFE_DIVIDE(vlr_venda_desconto, qt_material) AS desconto_por_item
FROM `{TABLE_ID}`
WHERE {DATE_FILTER}
  AND receita_aprovada = 0
  AND vlr_venda_desconto > 0
  AND SAFE_CAST(des_categoria_material AS NUMERIC) IS NULL
ORDER BY vlr_venda_desconto DESC
LIMIT 5
