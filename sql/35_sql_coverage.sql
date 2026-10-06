-- 35_sql_coverage.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 2.5 Cobertura temporal
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
horas_observadas AS (
  SELECT DISTINCT dt_hr_venda
  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
),
canais AS (
  SELECT des_canal_venda_final_agrup
  FROM UNNEST(['App', 'Site']) AS des_canal_venda_final_agrup
),
hora_canal_observado AS (
  SELECT DISTINCT
    dt_hr_venda,
    des_canal_venda_final_agrup
  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
),
faltas_hora_canal AS (
  SELECT h.dt_hr_venda, c.des_canal_venda_final_agrup
  FROM horas_esperadas h
  CROSS JOIN canais c
  LEFT JOIN hora_canal_observado o
    ON h.dt_hr_venda = o.dt_hr_venda
   AND c.des_canal_venda_final_agrup = o.des_canal_venda_final_agrup
  WHERE o.dt_hr_venda IS NULL
)
SELECT
  (SELECT COUNT(*) FROM horas_esperadas) AS horas_esperadas,
  (
    SELECT COUNT(*)
    FROM horas_esperadas h
    LEFT JOIN horas_observadas o USING (dt_hr_venda)
    WHERE o.dt_hr_venda IS NULL
  ) AS horas_sem_registro,
  (SELECT COUNT(*) FROM faltas_hora_canal) AS combinacoes_hora_canal_ausentes
