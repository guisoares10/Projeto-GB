-- 29_sql_negative_category_channel.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 2.4.3 Categoria × canal — concentração vs. taxa global
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

WITH base AS (
  SELECT
    IF(
      SAFE_CAST(des_categoria_material AS NUMERIC) IS NOT NULL,
      '__CATEGORIA_INVALIDA__',
      des_categoria_material
    ) AS des_categoria_material,
    des_canal_venda_final_agrup,
    receita_aprovada
  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
),
global_rate AS (
  SELECT
    SAFE_DIVIDE(
      COUNTIF(receita_aprovada < 0),
      COUNT(*)
    ) AS pct_negativa_global
  FROM base
),
grouped AS (
  SELECT
    des_categoria_material,
    des_canal_venda_final_agrup,
    COUNT(*) AS linhas,
    COUNTIF(receita_aprovada < 0) AS linhas_negativas,
    SAFE_DIVIDE(
      COUNTIF(receita_aprovada < 0),
      COUNT(*)
    ) AS pct_linhas_negativas,
    CAST(
      SUM(IF(receita_aprovada < 0, receita_aprovada, 0))
      AS FLOAT64
    ) AS receita_aprovada_negativa
  FROM base
  GROUP BY 1, 2
)
SELECT
  g.*,
  r.pct_negativa_global,
  100 * (g.pct_linhas_negativas - r.pct_negativa_global)
    AS diferenca_pp,
  SAFE_DIVIDE(
    g.pct_linhas_negativas,
    r.pct_negativa_global
  ) AS lift_vs_global,
  SAFE_DIVIDE(
    ABS(g.receita_aprovada_negativa),
    SUM(ABS(g.receita_aprovada_negativa)) OVER ()
  ) AS share_valor_negativo
FROM grouped g
CROSS JOIN global_rate r
ORDER BY ABS(g.pct_linhas_negativas - r.pct_negativa_global) DESC
