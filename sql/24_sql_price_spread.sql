-- case projeto GB
-- 24_sql_price_spread.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: E quando há 2 ou mais candidatas? O preço médio resolve?
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

SELECT
  des_categoria_material,
  COUNT(*) AS linhas,
  SAFE_DIVIDE(SUM(receita_aprovada), SUM(qt_material)) AS preco_medio_item,
  APPROX_QUANTILES(SAFE_DIVIDE(receita_aprovada, qt_material), 100)[OFFSET(10)] AS p10,
  APPROX_QUANTILES(SAFE_DIVIDE(receita_aprovada, qt_material), 100)[OFFSET(25)] AS p25,
  APPROX_QUANTILES(SAFE_DIVIDE(receita_aprovada, qt_material), 100)[OFFSET(50)] AS mediana,
  APPROX_QUANTILES(SAFE_DIVIDE(receita_aprovada, qt_material), 100)[OFFSET(75)] AS p75,
  APPROX_QUANTILES(SAFE_DIVIDE(receita_aprovada, qt_material), 100)[OFFSET(90)] AS p90
FROM `{TABLE_ID}`
WHERE {DATE_FILTER}
  AND SAFE_CAST(des_categoria_material AS NUMERIC) IS NULL
  AND receita_aprovada > 0
  AND qt_material > 0
GROUP BY 1
ORDER BY preco_medio_item
