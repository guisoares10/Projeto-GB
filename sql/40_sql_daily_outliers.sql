-- case projeto GB
-- 40_sql_daily_outliers.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 2.7 Outliers
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

WITH daily AS (
  SELECT
    DATE(dt_hr_venda) AS data,
    SUM(qt_material) AS qt_material,
    SUM(nr_pedidos) AS nr_pedidos,
    CAST(SUM(receita_aprovada) AS FLOAT64) AS receita_aprovada
  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
  GROUP BY 1
),
quartis AS (
  SELECT
    APPROX_QUANTILES(qt_material, 100)[OFFSET(25)] AS q1_qt_material,
    APPROX_QUANTILES(qt_material, 100)[OFFSET(75)] AS q3_qt_material,

    APPROX_QUANTILES(nr_pedidos, 100)[OFFSET(25)] AS q1_nr_pedidos,
    APPROX_QUANTILES(nr_pedidos, 100)[OFFSET(75)] AS q3_nr_pedidos,

    APPROX_QUANTILES(receita_aprovada, 100)[OFFSET(25)] AS q1_receita_aprovada,
    APPROX_QUANTILES(receita_aprovada, 100)[OFFSET(75)] AS q3_receita_aprovada
  FROM daily
),
limites AS (
  SELECT
    *,
    q1_qt_material - 1.5 * (q3_qt_material - q1_qt_material) AS li_qt_material,
    q3_qt_material + 1.5 * (q3_qt_material - q1_qt_material) AS ls_qt_material,

    q1_nr_pedidos - 1.5 * (q3_nr_pedidos - q1_nr_pedidos) AS li_nr_pedidos,
    q3_nr_pedidos + 1.5 * (q3_nr_pedidos - q1_nr_pedidos) AS ls_nr_pedidos,

    q1_receita_aprovada - 1.5 * (q3_receita_aprovada - q1_receita_aprovada) AS li_receita_aprovada,
    q3_receita_aprovada + 1.5 * (q3_receita_aprovada - q1_receita_aprovada) AS ls_receita_aprovada
  FROM quartis
)
SELECT
  l.*,

  COUNTIF(
    d.qt_material < l.li_qt_material
    OR d.qt_material > l.ls_qt_material
  ) AS dias_outlier_qt_material,

  COUNTIF(
    d.nr_pedidos < l.li_nr_pedidos
    OR d.nr_pedidos > l.ls_nr_pedidos
  ) AS dias_outlier_nr_pedidos,

  COUNTIF(
    d.receita_aprovada < l.li_receita_aprovada
    OR d.receita_aprovada > l.ls_receita_aprovada
  ) AS dias_outlier_receita_aprovada

FROM daily d
CROSS JOIN limites l
GROUP BY
  q1_qt_material, q3_qt_material,
  q1_nr_pedidos, q3_nr_pedidos,
  q1_receita_aprovada, q3_receita_aprovada,
  li_qt_material, ls_qt_material,
  li_nr_pedidos, ls_nr_pedidos,
  li_receita_aprovada, ls_receita_aprovada
