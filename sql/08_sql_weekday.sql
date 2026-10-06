-- 08_sql_weekday.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 1.5 Potencial de vendas por dia da semana
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

WITH daily AS (
  SELECT
    DATE(dt_hr_venda) AS data,

    CASE EXTRACT(DAYOFWEEK FROM DATE(dt_hr_venda))
      WHEN 2 THEN 0
      WHEN 3 THEN 1
      WHEN 4 THEN 2
      WHEN 5 THEN 3
      WHEN 6 THEN 4
      WHEN 7 THEN 5
      WHEN 1 THEN 6
    END AS dia_semana_num,

    CASE EXTRACT(DAYOFWEEK FROM DATE(dt_hr_venda))
      WHEN 2 THEN 'Segunda'
      WHEN 3 THEN 'Terça'
      WHEN 4 THEN 'Quarta'
      WHEN 5 THEN 'Quinta'
      WHEN 6 THEN 'Sexta'
      WHEN 7 THEN 'Sábado'
      WHEN 1 THEN 'Domingo'
    END AS dia_semana,

    SUM(qt_material) AS qt_material,
    SUM(nr_pedidos) AS nr_pedidos,
    CAST(SUM(receita_aprovada) AS FLOAT64) AS receita_aprovada

  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
  GROUP BY 1, 2, 3
),
global AS (
  SELECT
    APPROX_QUANTILES(qt_material, 100)[OFFSET(50)] AS mediana_global_qt_material
  FROM daily
)
SELECT
  d.dia_semana_num,
  d.dia_semana,
  COUNT(*) AS dias,
  AVG(d.qt_material) AS qt_material_media,
  APPROX_QUANTILES(d.qt_material, 100)[OFFSET(50)] AS qt_material_mediana,
  AVG(d.nr_pedidos) AS nr_pedidos_media,
  AVG(d.receita_aprovada) AS receita_aprovada_media,
  SAFE_DIVIDE(
    APPROX_QUANTILES(d.qt_material, 100)[OFFSET(50)],
    g.mediana_global_qt_material
  ) AS indice_potencial_qt_material
FROM daily d
CROSS JOIN global g
GROUP BY 1, 2, g.mediana_global_qt_material
ORDER BY 1
