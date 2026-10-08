-- 33_sql_negative_profile.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 2.4.7 É erro de sinal? E o desconto explica alguma coisa?
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

WITH base AS (
  SELECT
    IF(
      SAFE_CAST(des_categoria_material AS NUMERIC) IS NOT NULL,
      'CATEGORIA_INVALIDA',
      des_categoria_material
    ) AS des_categoria_material,
    IF(receita_aprovada < 0, 'NEGATIVA (sinal corrigido)', 'POSITIVA') AS grupo,
    ABS(receita_aprovada) AS receita_corrigida,
    vlr_venda_desconto,
    qt_material
  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
    AND receita_aprovada != 0
)
SELECT
  des_categoria_material,
  grupo,
  SAFE_DIVIDE(SUM(receita_corrigida), SUM(qt_material)) AS preco_medio_item,
  SAFE_DIVIDE(SUM(vlr_venda_desconto), SUM(qt_material)) AS desconto_por_item,
  SAFE_DIVIDE(SUM(vlr_venda_desconto), SUM(receita_corrigida + vlr_venda_desconto)) AS taxa_desconto
FROM base
GROUP BY 1, 2
