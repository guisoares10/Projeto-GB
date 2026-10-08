-- case projeto GB
-- 12_sql_hourly_category.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: Participação por hora por categoria — App × Site
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

WITH base AS (
  SELECT
    DATE(dt_hr_venda) AS data,
    EXTRACT(HOUR FROM dt_hr_venda) AS hora,
    des_canal_venda_final_agrup,
    des_categoria_material,
    SUM(qt_material) AS qt_material
  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
    AND SAFE_CAST(des_categoria_material AS NUMERIC) IS NULL
  GROUP BY 1, 2, 3, 4
),
dia AS (
  SELECT data, des_canal_venda_final_agrup, des_categoria_material, SUM(qt_material) AS qt_material_dia
  FROM base
  GROUP BY 1, 2, 3
  HAVING SUM(qt_material) > 0
),
n_dias AS (
  SELECT des_canal_venda_final_agrup, des_categoria_material, COUNT(*) AS n_dias
  FROM dia
  GROUP BY 1, 2
)
SELECT
  b.des_canal_venda_final_agrup,
  b.des_categoria_material,
  b.hora,
  SUM(SAFE_DIVIDE(b.qt_material, d.qt_material_dia)) / ANY_VALUE(n.n_dias) AS share_qt_material_media
FROM base b
JOIN dia d USING (data, des_canal_venda_final_agrup, des_categoria_material)
JOIN n_dias n USING (des_canal_venda_final_agrup, des_categoria_material)
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3
