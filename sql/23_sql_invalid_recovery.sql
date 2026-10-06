-- 23_sql_invalid_recovery.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 2.3.5 É possível recuperar as categorias inválidas?
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

WITH categorias AS (
  SELECT DISTINCT des_categoria_material
  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
    AND SAFE_CAST(des_categoria_material AS NUMERIC) IS NULL
),
invalidas AS (
  SELECT
    dt_hr_venda,
    des_canal_venda_final_agrup,
    des_categoria_material AS valor_invalido,
    qt_material,
    receita_aprovada
  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
    AND SAFE_CAST(des_categoria_material AS NUMERIC) IS NOT NULL
),
presentes AS (
  SELECT DISTINCT dt_hr_venda, des_canal_venda_final_agrup, des_categoria_material
  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
    AND SAFE_CAST(des_categoria_material AS NUMERIC) IS NULL
),
faltantes AS (
  -- todas as categorias possíveis, menos as que já aparecem naquela hora × canal
  SELECT i.*, c.des_categoria_material AS categoria_faltante
  FROM invalidas i
  CROSS JOIN categorias c
  LEFT JOIN presentes p
    ON  p.dt_hr_venda = i.dt_hr_venda
    AND p.des_canal_venda_final_agrup = i.des_canal_venda_final_agrup
    AND p.des_categoria_material = c.des_categoria_material
  WHERE p.des_categoria_material IS NULL
)
SELECT
  dt_hr_venda,
  des_canal_venda_final_agrup,
  valor_invalido,
  ANY_VALUE(qt_material) AS qt_material,
  ANY_VALUE(receita_aprovada) AS receita_aprovada,
  COUNT(*) AS n_candidatas,
  STRING_AGG(categoria_faltante, ' | ' ORDER BY categoria_faltante) AS categorias_candidatas,
  IF(COUNT(*) = 1, ANY_VALUE(categoria_faltante), NULL) AS categoria_recuperada
FROM faltantes
GROUP BY 1, 2, 3
