-- case projeto GB
-- 43_sql_conferencia_modelagem.sql
-- Usada no notebook modelo_machine_learning.ipynb, seção: 1. Base de modelagem
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID
--
-- Totais da tabela original, para conferir que a base de modelagem não
-- perdeu nem duplicou volume nas correções.

SELECT
  SUM(qt_material) AS qt_material,
  CAST(SUM(ROUND(ABS(receita_aprovada), 2)) AS FLOAT64) AS receita_aprovada,
  CAST(SUM(ROUND(vlr_venda_desconto, 2)) AS FLOAT64) AS vlr_venda_desconto,
  COUNTIF(SAFE_CAST(des_categoria_material AS NUMERIC) IS NOT NULL) AS linhas_categoria_invalida,
  SUM(IF(SAFE_CAST(des_categoria_material AS NUMERIC) IS NOT NULL, qt_material, 0)) AS qt_categoria_invalida
FROM `{TABLE_ID}`
WHERE {DATE_FILTER}
