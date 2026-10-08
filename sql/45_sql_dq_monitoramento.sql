-- 45_sql_dq_monitoramento.sql
-- Monitoramento da ingestão: mesmas regras da 41_sql_dq_checks.sql, com o desconto avaliado por categoria.
-- Usado na apresentação (slide de monitoramento), rodando de 01/12/2025 a 30/06/2026: novembro fica fora,
-- inclusive do histórico, por ser fora da curva (Black November).
-- Parâmetros: DATE_FILTER, END_DATE, LIMITE_DESCONTO_PP, START_DATE, TABLE_ID

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
    COALESCE(p.linhas_categoria_invalida, 0) AS linhas_categoria_invalida,
    COALESCE(p.linhas_receita_negativa, 0) AS linhas_receita_negativa,
    COALESCE(p.qt_material, 0) AS qt_material,
    -- histórico: mesma hora e dia da semana nas 4 semanas anteriores
    ARRAY_AGG(COALESCE(p.qt_material, 0)) OVER (
      PARTITION BY EXTRACT(HOUR FROM h.dt_hr_venda), EXTRACT(DAYOFWEEK FROM h.dt_hr_venda)
      ORDER BY h.dt_hr_venda ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING
    ) AS historico_qt_material
  FROM horas_esperadas h
  LEFT JOIN por_hora p USING (dt_hr_venda)
),
hora_com_esperado AS (
  SELECT
    * EXCEPT (historico_qt_material),
    ARRAY_LENGTH(historico_qt_material) AS semanas_historico,
    -- esperado: mediana do histórico (robusta a picos de campanha)
    (SELECT PERCENTILE_CONT(v, 0.5) OVER () FROM UNNEST(historico_qt_material) AS v LIMIT 1) AS qt_material_esperado
  FROM hora_completa
),
hora_com_volume AS (
  SELECT
    *,
    semanas_historico >= 3 AND qt_material_esperado >= 500
      AND (qt_material < 0.3 * qt_material_esperado OR qt_material > 3 * qt_material_esperado) AS hora_fora_do_esperado
  FROM hora_com_esperado
),
hora_final AS (
  SELECT
    *,
    -- anomalia sustentada: a hora e as 2 anteriores fora do esperado
    COUNTIF(hora_fora_do_esperado) OVER (ORDER BY dt_hr_venda ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) = 3 AS volume_sustentado
  FROM hora_com_volume
),
checks_hora AS (
  SELECT dt_hr_venda AS referencia, 'hora' AS frequencia, check_nome, severidade, falhou, detalhe
  FROM hora_final,
  UNNEST([
    STRUCT('nulos' AS check_nome, 'ERRO' AS severidade, linhas_com_nulo > 0 AS falhou,
           FORMAT('%d linhas com nulo', linhas_com_nulo) AS detalhe),
    STRUCT('dominio', 'ERRO', linhas_fora_dominio > 0, FORMAT('%d linhas fora do domínio', linhas_fora_dominio)),
    STRUCT('duplicidade_grao', 'ERRO', linhas_duplicadas > 0, FORMAT('%d linhas duplicadas', linhas_duplicadas)),
    STRUCT('hora_sem_dados', 'WARNING', linhas = 0, 'nenhuma linha na hora'),
    STRUCT('canal_ausente', 'WARNING', linhas > 0 AND canais_presentes < 2, FORMAT('%d de 2 canais', canais_presentes)),
    STRUCT('categoria_invalida', 'WARNING', linhas_categoria_invalida > 0,
           FORMAT('%d linha(s) com categoria numérica', linhas_categoria_invalida)),
    STRUCT('receita_negativa', 'WARNING', linhas_receita_negativa > 0,
           FORMAT('%d linha(s) com receita negativa', linhas_receita_negativa)),
    STRUCT('volume_anomalo_3h', 'WARNING', volume_sustentado,
           FORMAT('qt_material %d vs esperado %.0f', qt_material, qt_material_esperado))
  ])
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
dia_com_referencia AS (
  -- referência: últimos 28 dias fechados da mesma categoria (não inclui o próprio dia)
  SELECT
    *,
    COUNT(*) OVER w AS dias_historico,
    ARRAY_AGG(taxa_desconto_pp) OVER w AS historico_taxa_desconto
  FROM por_dia_categoria
  WINDOW w AS (PARTITION BY des_categoria_material ORDER BY data ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING)
),
checks_dia AS (
  SELECT CAST(data AS DATETIME) AS referencia, 'fechamento do dia' AS frequencia, check_nome, severidade, falhou, detalhe
  FROM (
    SELECT
      *,
      (SELECT PERCENTILE_CONT(v, 0.5) OVER () FROM UNNEST(historico_taxa_desconto) AS v LIMIT 1) AS taxa_desconto_esperada_pp
    FROM dia_com_referencia
  ),
  UNNEST([
    -- desconto da categoria fora de ±LIMITE_DESCONTO_PP p.p. da mediana dos 28 dias anteriores da própria categoria
    STRUCT('taxa_desconto_categoria' AS check_nome, 'WARNING' AS severidade,
           dias_historico >= 14 AND ABS(taxa_desconto_pp - taxa_desconto_esperada_pp) > {LIMITE_DESCONTO_PP} AS falhou,
           FORMAT('%s: %.1f%% vs esperado %.1f%%', des_categoria_material, taxa_desconto_pp, taxa_desconto_esperada_pp) AS detalhe)
  ])
)
SELECT * FROM checks_hora
UNION ALL
SELECT * FROM checks_dia
