-- 42_sql_base_modelagem.sql
-- Usada no notebook modelo_machine_learning.ipynb, seção: 1. Base de modelagem
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, END_DATE, START_DATE, TABLE_ID
--
-- Aplica as correções da análise exploratória e entrega o grão do modelo
-- (dia × canal × categoria), com a grade completa:
--   1. receita_aprovada negativa é erro de sinal -> ABS (seção 2.4);
--   2. receita e desconto com duas casas decimais -> ROUND(..., 2) (seção 2.6);
--   3. categoria inválida (código numérico) recebe a única categoria que falta
--      naquela hora × canal; com 2 ou mais candidatas vira NAO_IDENTIFICADA (seção 2.3.5);
--   4. dias sem venda de uma série entram com zero;
--   5. taxa_desconto_dia: taxa média do dia (todos os canais e categorias), a
--      premissa que o time de desconto informaria para os dias futuros.

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
diario AS (
  SELECT
    data,
    des_canal_venda_final_agrup,
    des_categoria_material,
    SUM(qt_material) AS qt_material,
    SUM(receita_aprovada) AS receita_aprovada,
    SUM(vlr_venda_desconto) AS vlr_venda_desconto
  FROM corrigido
  GROUP BY 1, 2, 3
),
grade AS (
  SELECT data, canal.des_canal_venda_final_agrup, cat.des_categoria_material
  FROM UNNEST(GENERATE_DATE_ARRAY(DATE '{START_DATE}', DATE '{END_DATE}')) AS data
  CROSS JOIN (SELECT DISTINCT des_canal_venda_final_agrup FROM diario) canal
  CROSS JOIN (SELECT DISTINCT des_categoria_material FROM diario) cat
)
SELECT
  g.data,
  g.des_canal_venda_final_agrup,
  g.des_categoria_material,
  COALESCE(d.qt_material, 0) AS qt_material,
  CAST(COALESCE(d.receita_aprovada, 0) AS FLOAT64) AS receita_aprovada,
  CAST(COALESCE(d.vlr_venda_desconto, 0) AS FLOAT64) AS vlr_venda_desconto,
  CAST(SAFE_DIVIDE(
    SUM(d.vlr_venda_desconto) OVER (PARTITION BY g.data),
    SUM(d.receita_aprovada + d.vlr_venda_desconto) OVER (PARTITION BY g.data)
  ) AS FLOAT64) AS taxa_desconto_dia
FROM grade g
LEFT JOIN diario d
  USING (data, des_canal_venda_final_agrup, des_categoria_material)
ORDER BY 1, 2, 3
