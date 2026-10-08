-- 20_sql_invalid_values_by_channel.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 2.3.3 Quais valores inválidos aparecem em cada canal?
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

WITH ranked AS (
  SELECT
    des_canal_venda_final_agrup,
    des_categoria_material AS valor_invalido,
    COUNT(*) AS linhas,

    ROW_NUMBER() OVER (
      PARTITION BY des_canal_venda_final_agrup
      ORDER BY COUNT(*) DESC, des_categoria_material
    ) AS rank_canal

  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
    AND SAFE_CAST(des_categoria_material AS NUMERIC) IS NOT NULL
  GROUP BY 1, 2
)
SELECT
  des_canal_venda_final_agrup,
  rank_canal,
  valor_invalido,
  linhas
FROM ranked
WHERE rank_canal <= 10
ORDER BY des_canal_venda_final_agrup, rank_canal
