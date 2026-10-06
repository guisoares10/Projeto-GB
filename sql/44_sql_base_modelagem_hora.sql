-- 44_sql_base_modelagem_hora.sql
-- Usada no notebook modelo_machine_learning_hora.ipynb, seção: 1. Base de modelagem
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, END_DATE, START_DATE, TABLE_ID
--
-- Mesmas correções de 42_sql_base_modelagem.sql, no grão hora × canal × categoria:
--   1. receita_aprovada negativa é erro de sinal -> ABS (seção 2.4);
--   2. receita e desconto com duas casas decimais -> ROUND(..., 2) (seção 2.6);
--   3. categoria inválida (código numérico) recebe a única categoria que falta
--      naquela hora × canal; com 2 ou mais candidatas vira NAO_IDENTIFICADA (seção 2.3.5);
--   4. horas sem venda de uma série entram com zero;
--   5. taxa_desconto_semana_categoria: taxa média de desconto da categoria na
--      semana (segunda a domingo, os dois canais juntos), a mesma premissa do
--      modelo diário.

WITH bruto AS (
  SELECT
    dt_hr_venda,
    des_canal_venda_final_agrup,
    des_categoria_material,
    SAFE_CAST(des_categoria_material AS NUMERIC) IS NOT NULL AS categoria_invalida,
    qt_material,
    ROUND(ABS(receita_aprovada), 2) AS receita_aprovada,
    ROUND(vlr_venda_desconto, 2) AS vlr_venda_desconto
  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
),
categorias AS (
  SELECT DISTINCT des_categoria_material
  FROM bruto
  WHERE NOT categoria_invalida
),
candidatas AS (
  -- para cada linha inválida: categorias que não aparecem naquela hora × canal
  SELECT
    i.dt_hr_venda,
    i.des_canal_venda_final_agrup,
    i.des_categoria_material AS valor_invalido,
    IF(COUNT(*) = 1, ANY_VALUE(c.des_categoria_material), NULL) AS categoria_recuperada
  FROM bruto i
  CROSS JOIN categorias c
  LEFT JOIN bruto p
    ON  p.dt_hr_venda = i.dt_hr_venda
    AND p.des_canal_venda_final_agrup = i.des_canal_venda_final_agrup
    AND p.des_categoria_material = c.des_categoria_material
  WHERE i.categoria_invalida
    AND p.des_categoria_material IS NULL
  GROUP BY 1, 2, 3
),
corrigido AS (
  SELECT
    DATETIME_TRUNC(b.dt_hr_venda, HOUR) AS hora,
    DATE(b.dt_hr_venda) AS data,
    b.des_canal_venda_final_agrup,
    CASE
      WHEN NOT b.categoria_invalida THEN b.des_categoria_material
      ELSE COALESCE(c.categoria_recuperada, 'NAO_IDENTIFICADA')
    END AS des_categoria_material,
    b.qt_material,
    b.receita_aprovada,
    b.vlr_venda_desconto
  FROM bruto b
  LEFT JOIN candidatas c
    ON  c.dt_hr_venda = b.dt_hr_venda
    AND c.des_canal_venda_final_agrup = b.des_canal_venda_final_agrup
    AND c.valor_invalido = b.des_categoria_material
),
por_hora AS (
  SELECT
    hora,
    data,
    des_canal_venda_final_agrup,
    des_categoria_material,
    SUM(qt_material) AS qt_material,
    SUM(receita_aprovada) AS receita_aprovada,
    SUM(vlr_venda_desconto) AS vlr_venda_desconto
  FROM corrigido
  GROUP BY 1, 2, 3, 4
),
grade AS (
  SELECT DATETIME(ts) AS hora, DATE(DATETIME(ts)) AS data, canal.des_canal_venda_final_agrup, cat.des_categoria_material
  FROM UNNEST(GENERATE_TIMESTAMP_ARRAY(TIMESTAMP '{START_DATE}', TIMESTAMP('{END_DATE} 23:00:00'), INTERVAL 1 HOUR)) AS ts
  CROSS JOIN (SELECT DISTINCT des_canal_venda_final_agrup FROM por_hora) canal
  CROSS JOIN (SELECT DISTINCT des_categoria_material FROM por_hora) cat
)
SELECT
  g.hora,
  g.data,
  g.des_canal_venda_final_agrup,
  g.des_categoria_material,
  COALESCE(d.qt_material, 0) AS qt_material,
  CAST(COALESCE(d.receita_aprovada, 0) AS FLOAT64) AS receita_aprovada,
  CAST(COALESCE(d.vlr_venda_desconto, 0) AS FLOAT64) AS vlr_venda_desconto,
  CAST(SAFE_DIVIDE(
    SUM(d.vlr_venda_desconto) OVER semana_categoria,
    SUM(d.receita_aprovada + d.vlr_venda_desconto) OVER semana_categoria
  ) AS FLOAT64) AS taxa_desconto_semana_categoria
FROM grade g
LEFT JOIN por_hora d
  USING (hora, data, des_canal_venda_final_agrup, des_categoria_material)
WINDOW semana_categoria AS (
  PARTITION BY DATE_TRUNC(g.data, WEEK(MONDAY)), g.des_categoria_material
)
ORDER BY 1, 3, 4
