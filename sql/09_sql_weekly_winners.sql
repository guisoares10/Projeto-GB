-- 09_sql_weekly_winners.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: Qual dia vence em cada semana?
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

WITH daily AS (
  SELECT
    DATE(dt_hr_venda) AS data,
    DATE_TRUNC(DATE(dt_hr_venda), WEEK(MONDAY)) AS semana_inicio,

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

    SUM(qt_material) AS qt_material

  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
  GROUP BY 1, 2, 3, 4
),
ranked AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY semana_inicio
      ORDER BY qt_material DESC, data
    ) AS rn
  FROM daily
)
SELECT
  semana_inicio,
  data,
  dia_semana_num,
  dia_semana,
  qt_material
FROM ranked
WHERE rn = 1
ORDER BY semana_inicio
