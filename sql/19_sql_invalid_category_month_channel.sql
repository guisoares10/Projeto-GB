-- case projeto GB
-- 19_sql_invalid_category_month_channel.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 2.3.2 A concentração muda ao longo dos meses?
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

SELECT
  DATE_TRUNC(DATE(dt_hr_venda), MONTH) AS mes,
  des_canal_venda_final_agrup,

  COUNT(*) AS linhas,

  COUNTIF(
    SAFE_CAST(des_categoria_material AS NUMERIC) IS NOT NULL
  ) AS categorias_invalidas,

  SAFE_DIVIDE(
    COUNTIF(
      SAFE_CAST(des_categoria_material AS NUMERIC) IS NOT NULL
    ),
    COUNT(*)
  ) AS pct_categoria_invalida

FROM `{TABLE_ID}`
WHERE {DATE_FILTER}
GROUP BY 1, 2
ORDER BY 1, 2
