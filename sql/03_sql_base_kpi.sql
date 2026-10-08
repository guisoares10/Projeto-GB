-- case projeto GB
-- 03_sql_base_kpi.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: Base dos KPIs e funções de visualização
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

SELECT
  DATE_TRUNC(DATE(dt_hr_venda), MONTH) AS mes,
  des_canal_venda_final_agrup,
  IF(
    SAFE_CAST(des_categoria_material AS NUMERIC) IS NOT NULL,
    'CATEGORIA_INVALIDA',
    des_categoria_material
  ) AS des_categoria_material,
  SUM(qt_material) AS qt_material,
  SUM(nr_pedidos) AS nr_pedidos,
  CAST(SUM(receita_aprovada) AS FLOAT64) AS receita_aprovada,
  CAST(SUM(vlr_venda_desconto) AS FLOAT64) AS vlr_venda_desconto
FROM `{TABLE_ID}`
WHERE {DATE_FILTER}
GROUP BY 1, 2, 3
