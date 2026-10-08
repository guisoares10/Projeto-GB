-- case projeto GB
-- 01_sql_overview.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 1. Dados — fonte, schema e período
-- Parâmetros preenchidos por carregar_sql(): TABLE_ID

SELECT
  COUNT(*) AS linhas,
  MIN(dt_hr_venda) AS dt_min,
  MAX(dt_hr_venda) AS dt_max,
  COUNT(DISTINCT DATE(dt_hr_venda)) AS dias,
  COUNT(DISTINCT des_canal_venda_final_agrup) AS canais,
  COUNT(DISTINCT des_categoria_material) AS categorias_brutas
FROM `{TABLE_ID}`
WHERE 1=1
