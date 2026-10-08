-- case projeto GB
-- 11_sql_hourly_channel.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: Participação por hora — App × Site
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

WITH base AS (
  SELECT
    DATE(dt_hr_venda) AS data,
    EXTRACT(HOUR FROM dt_hr_venda) AS hora,
    des_canal_venda_final_agrup,
    SUM(qt_material) AS qt_material
  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
  GROUP BY 1, 2, 3
),
dia AS (
  SELECT data, des_canal_venda_final_agrup, SUM(qt_material) AS qt_material_dia
  FROM base
  GROUP BY 1, 2
  HAVING SUM(qt_material) > 0
),
n_dias AS (
  SELECT des_canal_venda_final_agrup, COUNT(*) AS n_dias
  FROM dia
  GROUP BY 1
)
SELECT
  b.des_canal_venda_final_agrup,
  b.hora,
  -- soma das participações / nº de dias: horas sem venda entram como zero
  SUM(SAFE_DIVIDE(b.qt_material, d.qt_material_dia)) / ANY_VALUE(n.n_dias) AS share_qt_material_media
FROM base b
JOIN dia d USING (data, des_canal_venda_final_agrup)
JOIN n_dias n USING (des_canal_venda_final_agrup)
GROUP BY 1, 2
ORDER BY 1, 2
