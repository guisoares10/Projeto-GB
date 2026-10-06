-- Preparação da camada BigQuery para o Case Técnico | Especialista de Dados I
--
-- Objetivo:
-- 1) preservar a primeira carga em stg_fact_vendas;
-- 2) reconstruir fact_vendas com campos monetários decimais truncados a 2 casas;
-- 3) manter o processo idempotente e auditável.
--
-- Decisão de tipagem:
-- NUMERIC é intencional para valores monetários. BIGNUMERIC não é necessário:
-- as casas adicionais observadas (ex.: 3731.5600000000004) são artefatos de ponto
-- flutuante, não precisão financeira relevante.

-- 0. Diagnóstico do schema atual
SELECT
  column_name,
  data_type,
  is_nullable
FROM `gms-prod-01.projeto_gb.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'fact_vendas'
ORDER BY ordinal_position;

-- 1. Preserva a carga original.
-- CREATE TABLE IF NOT EXISTS evita sobrescrever o staging em reexecuções.
CREATE TABLE IF NOT EXISTS `gms-prod-01.projeto_gb.stg_fact_vendas` AS
SELECT *
FROM `gms-prod-01.projeto_gb.fact_vendas`;

-- 2. Validação antes da conversão.
-- O resultado esperado para *_falha_cast é zero.
SELECT
  COUNT(*) AS linhas,
  COUNTIF(
    receita_aprovada IS NOT NULL
    AND SAFE_CAST(receita_aprovada AS NUMERIC) IS NULL
  ) AS receita_falha_cast,
  COUNTIF(
    vlr_venda_desconto IS NOT NULL
    AND SAFE_CAST(vlr_venda_desconto AS NUMERIC) IS NULL
  ) AS desconto_falha_cast
FROM `gms-prod-01.projeto_gb.stg_fact_vendas`;

-- 3. Recria a fact tratada.
-- Primeiro convertemos para NUMERIC (decimal exato) e então truncamos para
-- duas casas, que é a granularidade de negócio adotada para moeda.
CREATE OR REPLACE TABLE `gms-prod-01.projeto_gb.fact_vendas` AS
SELECT
  * REPLACE (
    TRUNC(SAFE_CAST(receita_aprovada AS NUMERIC), 2) AS receita_aprovada,
    TRUNC(SAFE_CAST(vlr_venda_desconto AS NUMERIC), 2) AS vlr_venda_desconto
  )
FROM `gms-prod-01.projeto_gb.stg_fact_vendas`;

-- 4. Checks pós-tratamento.
SELECT
  COUNT(*) AS linhas,
  COUNTIF(receita_aprovada IS NULL) AS receita_nula,
  COUNTIF(vlr_venda_desconto IS NULL) AS desconto_nulo,
  COUNTIF(receita_aprovada != ROUND(receita_aprovada, 2)) AS receita_acima_2_casas,
  COUNTIF(vlr_venda_desconto != ROUND(vlr_venda_desconto, 2)) AS desconto_acima_2_casas
FROM `gms-prod-01.projeto_gb.fact_vendas`;

-- 5. Confirma os tipos finais.
SELECT
  column_name,
  data_type
FROM `gms-prod-01.projeto_gb.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'fact_vendas'
  AND column_name IN ('receita_aprovada', 'vlr_venda_desconto')
ORDER BY column_name;
