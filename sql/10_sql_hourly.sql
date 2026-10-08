-- case projeto GB
-- 10_sql_hourly.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 1.6 Horários — flutuação ao longo do dia
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

WITH hourly_daily AS (
  SELECT
    DATE(dt_hr_venda) AS data,
    EXTRACT(HOUR FROM dt_hr_venda) AS hora,
    CAST(SUM(receita_aprovada) AS FLOAT64) AS receita_aprovada,
    SUM(nr_pedidos) AS nr_pedidos,
    SUM(qt_material) AS qt_material
  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
  GROUP BY 1, 2
),
shares AS (
  SELECT
    *,
    SAFE_DIVIDE(receita_aprovada, SUM(receita_aprovada) OVER (PARTITION BY data)) AS share_receita_aprovada,
    SAFE_DIVIDE(qt_material, SUM(qt_material) OVER (PARTITION BY data)) AS share_qt_material
  FROM hourly_daily
)
SELECT
  hora,
  AVG(receita_aprovada) AS receita_aprovada_media,
  AVG(nr_pedidos) AS nr_pedidos_media,
  AVG(qt_material) AS qt_material_media,
  AVG(share_receita_aprovada) AS share_receita_aprovada_media,
  AVG(share_qt_material) AS share_qt_material_media
FROM shares
GROUP BY 1
ORDER BY 1
