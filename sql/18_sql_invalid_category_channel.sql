-- 18_sql_invalid_category_channel.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 2.3.1 A categoria inválida se concentra em App ou Site?
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

WITH base AS (
  SELECT
    des_canal_venda_final_agrup,
    SAFE_CAST(des_categoria_material AS NUMERIC) IS NOT NULL
      AS categoria_invalida
  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
),
global_rate AS (
  SELECT
    SAFE_DIVIDE(
      COUNTIF(categoria_invalida),
      COUNT(*)
    ) AS pct_invalida_global
  FROM base
),
by_channel AS (
  SELECT
    des_canal_venda_final_agrup,
    COUNT(*) AS linhas,
    COUNTIF(categoria_invalida) AS categorias_invalidas,
    SAFE_DIVIDE(
      COUNTIF(categoria_invalida),
      COUNT(*)
    ) AS pct_categoria_invalida
  FROM base
  GROUP BY 1
)
SELECT
  b.*,
  g.pct_invalida_global,

  SAFE_DIVIDE(
    b.pct_categoria_invalida,
    g.pct_invalida_global
  ) AS lift_vs_global,

  SAFE_DIVIDE(
    b.categorias_invalidas,
    SUM(b.categorias_invalidas) OVER ()
  ) AS share_dos_invalidos

FROM by_channel b
CROSS JOIN global_rate g
ORDER BY pct_categoria_invalida DESC
