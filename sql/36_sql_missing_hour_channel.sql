-- case projeto GB
-- 36_sql_missing_hour_channel.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: Combinações hora × canal ausentes
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, END_DATE, START_DATE, TABLE_ID

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
  SELECT DISTINCT
    dt_hr_venda,
    des_canal_venda_final_agrup
  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
)
SELECT
  h.dt_hr_venda,
  c.des_canal_venda_final_agrup
FROM horas_esperadas h
CROSS JOIN canais c
LEFT JOIN observado o
  ON h.dt_hr_venda = o.dt_hr_venda
 AND c.des_canal_venda_final_agrup = o.des_canal_venda_final_agrup
WHERE o.dt_hr_venda IS NULL
ORDER BY h.dt_hr_venda, c.des_canal_venda_final_agrup
LIMIT 100
