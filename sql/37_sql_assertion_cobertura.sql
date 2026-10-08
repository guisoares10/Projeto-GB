-- 37_sql_assertion_cobertura.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: Assertion de cobertura: horas sem informação
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, END_DATE, START_DATE, TABLE_ID

-- Assertion (warning): retorna as combinações hora x canal sem nenhuma linha no período
WITH horas_esperadas AS (
  SELECT DATETIME(ts) AS dt_hr_venda
  FROM UNNEST(
    GENERATE_TIMESTAMP_ARRAY(
      TIMESTAMP('{START_DATE} 00:00:00'),
      TIMESTAMP('{END_DATE} 23:00:00'),
      INTERVAL 1 HOUR
    )
  ) AS ts
),
canais AS (
  SELECT des_canal_venda_final_agrup
  FROM UNNEST(['App', 'Site']) AS des_canal_venda_final_agrup
),
observado AS (
  SELECT
    dt_hr_venda,
    des_canal_venda_final_agrup,
    SUM(qt_material) AS qt_material
  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
  GROUP BY 1, 2
),
volume_tipico AS (
  -- mediana de qt_material da mesma hora do dia e canal, para triagem
  SELECT
    EXTRACT(HOUR FROM dt_hr_venda) AS hora,
    des_canal_venda_final_agrup,
    APPROX_QUANTILES(qt_material, 100)[OFFSET(50)] AS qt_material_mediana_hora
  FROM observado
  GROUP BY 1, 2
)
SELECT
  h.dt_hr_venda,
  c.des_canal_venda_final_agrup,
  v.qt_material_mediana_hora,
  'WARNING' AS severidade,
  IF(
    v.qt_material_mediana_hora < 50,
    'hora de baixo volume: provável ausência de vendas',
    'hora com volume relevante: verificar pipeline'
  ) AS triagem
FROM horas_esperadas h
CROSS JOIN canais c
LEFT JOIN observado o
  ON  o.dt_hr_venda = h.dt_hr_venda
  AND o.des_canal_venda_final_agrup = c.des_canal_venda_final_agrup
LEFT JOIN volume_tipico v
  ON  v.hora = EXTRACT(HOUR FROM h.dt_hr_venda)
  AND v.des_canal_venda_final_agrup = c.des_canal_venda_final_agrup
WHERE o.dt_hr_venda IS NULL
ORDER BY h.dt_hr_venda
