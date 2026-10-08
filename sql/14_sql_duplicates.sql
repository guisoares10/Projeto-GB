-- 14_sql_duplicates.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 2.2 Duplicidade no grão
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

WITH duplicados AS (
  SELECT
    dt_hr_venda,
    des_canal_venda_final_agrup,
    des_categoria_material,
    COUNT(*) AS qtd
  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
  GROUP BY 1, 2, 3
  HAVING COUNT(*) > 1
)
SELECT
  COUNT(*) AS grupos_duplicados,
  COALESCE(SUM(qtd - 1), 0) AS linhas_excedentes
FROM duplicados
