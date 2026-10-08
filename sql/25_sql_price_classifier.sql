-- 25_sql_price_classifier.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: E quando há 2 ou mais candidatas? O preço médio resolve?
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

WITH preco_ref AS (
  SELECT
    DATE_TRUNC(DATE(dt_hr_venda), MONTH) AS mes,
    des_canal_venda_final_agrup,
    des_categoria_material,
    SAFE_DIVIDE(SUM(receita_aprovada), SUM(qt_material)) AS preco_ref
  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
    AND SAFE_CAST(des_categoria_material AS NUMERIC) IS NULL
    AND receita_aprovada > 0
  GROUP BY 1, 2, 3
),
validas AS (
  SELECT
    FARM_FINGERPRINT(CONCAT(CAST(dt_hr_venda AS STRING), des_canal_venda_final_agrup, des_categoria_material)) AS id_linha,
    DATE_TRUNC(DATE(dt_hr_venda), MONTH) AS mes,
    des_canal_venda_final_agrup,
    des_categoria_material AS categoria_real,
    SAFE_DIVIDE(receita_aprovada, qt_material) AS preco_linha
  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
    AND SAFE_CAST(des_categoria_material AS NUMERIC) IS NULL
    AND receita_aprovada > 0
    AND qt_material > 0
),
distancias AS (
  -- distância (em log) entre o preço da linha e o preço de referência de cada categoria
  SELECT
    v.id_linha,
    v.categoria_real,
    r.des_categoria_material AS categoria_comparada,
    ABS(LN(v.preco_linha / r.preco_ref)) AS distancia
  FROM validas v
  JOIN preco_ref r
    ON  r.mes = v.mes
    AND r.des_canal_venda_final_agrup = v.des_canal_venda_final_agrup
),
mais_proxima AS (
  -- categoria com preço de referência mais próximo de cada linha
  SELECT *
  FROM distancias
  WHERE TRUE
  QUALIFY ROW_NUMBER() OVER (PARTITION BY id_linha ORDER BY distancia) = 1
),
entre_8 AS (
  SELECT
    COUNT(*) AS linhas,
    AVG(IF(categoria_comparada = categoria_real, 1, 0)) AS acerto
  FROM mais_proxima
),
entre_2 AS (
  -- cada linha válida contra cada uma das outras 7 categorias
  SELECT
    COUNT(*) AS pares,
    AVG(IF(real.distancia < outra.distancia, 1, 0)) AS acerto
  FROM distancias real
  JOIN distancias outra
    ON  outra.id_linha = real.id_linha
    AND outra.categoria_comparada != real.categoria_real
  WHERE real.categoria_comparada = real.categoria_real
)
SELECT 'Escolher entre 8 categorias' AS cenario, linhas AS comparacoes, acerto, 1 / 8 AS acerto_por_acaso FROM entre_8
UNION ALL
SELECT 'Escolher entre 2 categorias', pares, acerto, 1 / 2 FROM entre_2
