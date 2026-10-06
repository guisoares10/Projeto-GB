-- 16_sql_invalid_category_top10.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: Exemplos das categorias inválidas
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

SELECT
  des_categoria_material AS categoria_invalida,
  COUNT(*) AS linhas,
  SUM(qt_material) AS qt_material,
  CAST(SUM(receita_aprovada) AS FLOAT64) AS receita_aprovada
FROM `{TABLE_ID}`
WHERE {DATE_FILTER}
  AND SAFE_CAST(des_categoria_material AS NUMERIC) IS NOT NULL
GROUP BY 1
ORDER BY linhas DESC, categoria_invalida
LIMIT 10
