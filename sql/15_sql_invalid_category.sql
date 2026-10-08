-- 15_sql_invalid_category.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 2.3 Categoria inválida
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

SELECT
  COUNT(*) AS linhas,
  COUNTIF(SAFE_CAST(des_categoria_material AS NUMERIC) IS NOT NULL) AS categorias_invalidas,
  SAFE_DIVIDE(
    COUNTIF(SAFE_CAST(des_categoria_material AS NUMERIC) IS NOT NULL),
    COUNT(*)
  ) AS pct_categoria_invalida,
  COUNT(DISTINCT IF(
    SAFE_CAST(des_categoria_material AS NUMERIC) IS NULL,
    des_categoria_material,
    NULL
  )) AS categorias_validas_distintas
FROM `{TABLE_ID}`
WHERE {DATE_FILTER}
