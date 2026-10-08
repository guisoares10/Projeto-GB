-- case projeto GB
-- 17_sql_invalid_category_month.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: Exemplos das categorias inválidas
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

SELECT
  FORMAT_DATE('%Y-%m', DATE(dt_hr_venda)) AS mes,
  COUNT(*) AS linhas,
  COUNTIF(SAFE_CAST(des_categoria_material AS NUMERIC) IS NOT NULL) AS categorias_invalidas,
  SAFE_DIVIDE(
    COUNTIF(SAFE_CAST(des_categoria_material AS NUMERIC) IS NOT NULL),
    COUNT(*)
  ) AS pct_invalida
FROM `{TABLE_ID}`
WHERE {DATE_FILTER}
GROUP BY 1
ORDER BY 1
