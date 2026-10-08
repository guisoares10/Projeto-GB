-- 28_sql_negative_by_category.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 2.4.2 Existe padrão por categoria?
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

WITH base AS (
  SELECT
    IF(
      SAFE_CAST(des_categoria_material AS NUMERIC) IS NOT NULL,
      '__CATEGORIA_INVALIDA__',
      des_categoria_material
    ) AS des_categoria_material,
    receita_aprovada
  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
)
SELECT
  des_categoria_material,
  COUNT(*) AS linhas,
  COUNTIF(receita_aprovada < 0) AS linhas_negativas,
  SAFE_DIVIDE(
    COUNTIF(receita_aprovada < 0),
    COUNT(*)
  ) AS pct_linhas_negativas,

  CAST(SUM(IF(receita_aprovada < 0, receita_aprovada, 0)) AS FLOAT64)
    AS receita_aprovada_negativa,

  CAST(SUM(IF(receita_aprovada >= 0, receita_aprovada, 0)) AS FLOAT64)
    AS receita_aprovada_positiva,

  SAFE_DIVIDE(
    -CAST(SUM(IF(receita_aprovada < 0, receita_aprovada, 0)) AS FLOAT64),
    CAST(SUM(IF(receita_aprovada >= 0, receita_aprovada, 0)) AS FLOAT64)
  ) AS impacto_negativo_sobre_positivo

FROM base
GROUP BY 1
ORDER BY ABS(receita_aprovada_negativa) DESC
