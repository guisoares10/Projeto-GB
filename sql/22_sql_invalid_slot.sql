-- case projeto GB
-- 22_sql_invalid_slot.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 2.3.5 É possível recuperar as categorias inválidas?
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

WITH slot AS (
  SELECT
    dt_hr_venda,
    des_canal_venda_final_agrup,
    COUNTIF(SAFE_CAST(des_categoria_material AS NUMERIC) IS NULL)     AS categorias_validas,
    COUNTIF(SAFE_CAST(des_categoria_material AS NUMERIC) IS NOT NULL) AS categorias_invalidas
  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
  GROUP BY 1, 2
)
SELECT
  categorias_validas,
  categorias_invalidas,
  categorias_validas + categorias_invalidas AS total_linhas_no_slot,
  COUNT(*) AS slots_hora_canal
FROM slot
GROUP BY 1, 2
ORDER BY 1 DESC, 2
