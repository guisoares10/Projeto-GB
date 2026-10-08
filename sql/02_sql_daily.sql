-- case projeto GB
-- 02_sql_daily.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: Série diária (base para as seções 3 e 4)
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

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

  FORMAT_DATE('%Y-%m', DATE(dt_hr_venda)) AS mes,
  EXTRACT(MONTH FROM DATE(dt_hr_venda)) AS mes_num,
  EXTRACT(YEAR FROM DATE(dt_hr_venda)) AS ano,
  EXTRACT(ISOWEEK FROM DATE(dt_hr_venda)) AS semana_ano,
  EXTRACT(ISOYEAR FROM DATE(dt_hr_venda)) AS ano_iso,
  DATE_TRUNC(DATE(dt_hr_venda), WEEK(MONDAY)) AS semana_inicio,
  IF(EXTRACT(DAYOFWEEK FROM DATE(dt_hr_venda)) IN (1, 7), 1, 0) AS fim_de_semana,

  CAST(SUM(receita_aprovada) AS FLOAT64) AS receita_aprovada,
  SUM(nr_pedidos) AS nr_pedidos,
  SUM(qt_material) AS qt_material,
  CAST(SUM(vlr_venda_desconto) AS FLOAT64) AS vlr_venda_desconto,

  SAFE_DIVIDE(
    CAST(SUM(receita_aprovada) AS FLOAT64),
    SUM(qt_material)
  ) AS preco_medio_item,

  SAFE_DIVIDE(
    CAST(SUM(receita_aprovada) AS FLOAT64),
    SUM(nr_pedidos)
  ) AS ticket_medio,

  SAFE_DIVIDE(
    SUM(qt_material),
    SUM(nr_pedidos)
  ) AS itens_por_pedido,

  SAFE_DIVIDE(
    CAST(SUM(vlr_venda_desconto) AS FLOAT64),
    CAST(SUM(receita_aprovada + vlr_venda_desconto) AS FLOAT64)
  ) AS taxa_desconto

FROM `{TABLE_ID}`
WHERE {DATE_FILTER}
GROUP BY ALL
ORDER BY 1
