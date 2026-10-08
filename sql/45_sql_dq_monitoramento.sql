-- 45_sql_dq_monitoramento.sql
-- Monitoramento da ingestão: checks estruturais por carga horária (como na 41_sql_dq_checks.sql) e,
-- no fechamento do dia, outliers pelo IQR expansivo (Q1 − 1,5 × IQR e Q3 + 1,5 × IQR calculados só com os dias
-- anteriores): volume diário de itens e taxa de desconto por categoria.
-- Usado na apresentação (slide de monitoramento), rodando de 01/12/2025 a 30/06/2026: novembro fica fora,
-- inclusive do histórico, por ser fora da curva (Black November).
-- Parâmetros: DATE_FILTER, END_DATE, MIN_DIAS_HISTORICO, START_DATE, TABLE_ID

WITH horas_esperadas AS (
  SELECT DATETIME(ts) AS dt_hr_venda
  FROM UNNEST(GENERATE_TIMESTAMP_ARRAY(
    TIMESTAMP('{START_DATE} 00:00:00'), TIMESTAMP('{END_DATE} 23:00:00'), INTERVAL 1 HOUR)) AS ts
),
por_hora AS (
  SELECT
    dt_hr_venda,
    COUNT(*) AS linhas,
    COUNTIF(des_canal_venda_final_agrup IS NULL OR des_categoria_material IS NULL OR receita_aprovada IS NULL
            OR nr_pedidos IS NULL OR qt_material IS NULL OR vlr_venda_desconto IS NULL) AS linhas_com_nulo,
    COUNTIF(des_canal_venda_final_agrup NOT IN ('App', 'Site') OR qt_material <= 0 OR nr_pedidos <= 0) AS linhas_fora_dominio,
    COUNT(*) - COUNT(DISTINCT CONCAT(des_canal_venda_final_agrup, '|', des_categoria_material)) AS linhas_duplicadas,
    COUNT(DISTINCT des_canal_venda_final_agrup) AS canais_presentes,
    -- linhas por canal: o grão tem 1 linha por categoria, então 8 linhas por canal (categoria inválida conta, é uma das 8 sem nome)
    COUNTIF(des_canal_venda_final_agrup = 'App') AS linhas_app,
    COUNTIF(des_canal_venda_final_agrup = 'Site') AS linhas_site,
    COUNTIF(SAFE_CAST(des_categoria_material AS NUMERIC) IS NOT NULL) AS linhas_categoria_invalida,
    COUNTIF(receita_aprovada < 0) AS linhas_receita_negativa,
    SUM(qt_material) AS qt_material
  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
  GROUP BY 1
),
hora_completa AS (
  SELECT
    h.dt_hr_venda,
    COALESCE(p.linhas, 0) AS linhas,
    COALESCE(p.linhas_com_nulo, 0) AS linhas_com_nulo,
    COALESCE(p.linhas_fora_dominio, 0) AS linhas_fora_dominio,
    COALESCE(p.linhas_duplicadas, 0) AS linhas_duplicadas,
    COALESCE(p.canais_presentes, 0) AS canais_presentes,
    COALESCE(p.linhas_app, 0) AS linhas_app,
    COALESCE(p.linhas_site, 0) AS linhas_site,
    COALESCE(p.linhas_categoria_invalida, 0) AS linhas_categoria_invalida,
    COALESCE(p.linhas_receita_negativa, 0) AS linhas_receita_negativa,
    COALESCE(p.qt_material, 0) AS qt_material
  FROM horas_esperadas h
  LEFT JOIN por_hora p USING (dt_hr_venda)
),
checks_hora AS (
  SELECT dt_hr_venda AS referencia, 'hora' AS frequencia, check_nome, severidade, falhou, detalhe
  FROM hora_completa,
  UNNEST([
    STRUCT('nulos' AS check_nome, 'ERRO' AS severidade, linhas_com_nulo > 0 AS falhou,
           FORMAT('%d linhas com nulo', linhas_com_nulo) AS detalhe),
    STRUCT('dominio', 'ERRO', linhas_fora_dominio > 0, FORMAT('%d linhas fora do domínio', linhas_fora_dominio)),
    STRUCT('duplicidade_grao', 'ERRO', linhas_duplicadas > 0, FORMAT('%d linhas duplicadas', linhas_duplicadas)),
    STRUCT('hora_sem_dados', 'WARNING', linhas = 0, 'nenhuma linha na hora'),
    STRUCT('canal_ausente', 'WARNING', linhas > 0 AND canais_presentes < 2, FORMAT('%d de 2 canais', canais_presentes)),
    STRUCT('categoria_ausente', 'WARNING', linhas > 0 AND (linhas_app < 8 OR linhas_site < 8),
           FORMAT('App %d de 8 categorias, Site %d de 8', linhas_app, linhas_site)),
    STRUCT('categoria_invalida', 'WARNING', linhas_categoria_invalida > 0,
           FORMAT('%d linha(s) com categoria numérica', linhas_categoria_invalida)),
    STRUCT('receita_negativa', 'WARNING', linhas_receita_negativa > 0,
           FORMAT('%d linha(s) com receita negativa', linhas_receita_negativa))
  ])
),
por_dia AS (
  SELECT DATE(dt_hr_venda) AS data, SUM(qt_material) AS qt_material
  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER}
  GROUP BY 1
),
por_dia_categoria AS (
  -- taxa de desconto do dia por categoria válida (categoria inválida tem check próprio)
  SELECT
    DATE(dt_hr_venda) AS data,
    des_categoria_material,
    100 * SAFE_DIVIDE(SUM(vlr_venda_desconto), SUM(receita_aprovada + vlr_venda_desconto)) AS taxa_desconto_pp
  FROM `{TABLE_ID}`
  WHERE {DATE_FILTER} AND SAFE_CAST(des_categoria_material AS NUMERIC) IS NULL
  GROUP BY 1, 2
),
volume_com_historico AS (
  -- IQR expansivo: todos os dias anteriores (o próprio dia fica de fora)
  SELECT *, ARRAY_AGG(qt_material) OVER (ORDER BY data ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS historico
  FROM por_dia
),
desconto_com_historico AS (
  SELECT *, ARRAY_AGG(taxa_desconto_pp) OVER (
    PARTITION BY des_categoria_material ORDER BY data ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS historico
  FROM por_dia_categoria
),
volume_limites AS (
  SELECT
    data, qt_material AS valor, ARRAY_LENGTH(historico) AS dias_historico,
    (SELECT PERCENTILE_CONT(v, 0.25) OVER () FROM UNNEST(historico) AS v LIMIT 1) AS q1,
    (SELECT PERCENTILE_CONT(v, 0.75) OVER () FROM UNNEST(historico) AS v LIMIT 1) AS q3
  FROM volume_com_historico
),
desconto_limites AS (
  SELECT
    data, des_categoria_material, taxa_desconto_pp AS valor, ARRAY_LENGTH(historico) AS dias_historico,
    (SELECT PERCENTILE_CONT(v, 0.25) OVER () FROM UNNEST(historico) AS v LIMIT 1) AS q1,
    (SELECT PERCENTILE_CONT(v, 0.75) OVER () FROM UNNEST(historico) AS v LIMIT 1) AS q3
  FROM desconto_com_historico
),
checks_dia AS (
  SELECT
    CAST(data AS DATETIME) AS referencia, 'fechamento do dia' AS frequencia, 'volume_outlier_iqr' AS check_nome,
    'WARNING' AS severidade,
    dias_historico >= {MIN_DIAS_HISTORICO}
      AND (valor < q1 - 1.5 * (q3 - q1) OR valor > q3 + 1.5 * (q3 - q1)) AS falhou,
    FORMAT('qt_material %d fora de [%.0f; %.0f]', CAST(valor AS INT64), q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)) AS detalhe
  FROM volume_limites
  UNION ALL
  SELECT
    CAST(data AS DATETIME), 'fechamento do dia', 'desconto_outlier_iqr', 'WARNING',
    dias_historico >= {MIN_DIAS_HISTORICO}
      AND (valor < q1 - 1.5 * (q3 - q1) OR valor > q3 + 1.5 * (q3 - q1)),
    FORMAT('%s: %.1f%% fora de [%.1f%%; %.1f%%]', des_categoria_material, valor,
           q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1))
  FROM desconto_limites
)
SELECT * FROM checks_hora
UNION ALL
SELECT * FROM checks_dia
