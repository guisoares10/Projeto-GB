-- 13_sql_quality.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 2.1 Nulos, domínios e valores impossíveis
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

SELECT
  COUNT(*) AS linhas,

  COUNTIF(dt_hr_venda IS NULL) AS dt_hr_venda_nulos,
  COUNTIF(des_canal_venda_final_agrup IS NULL) AS canal_nulos,
  COUNTIF(des_categoria_material IS NULL) AS categoria_nulos,
  COUNTIF(receita_aprovada IS NULL) AS receita_aprovada_nulos,
  COUNTIF(nr_pedidos IS NULL) AS nr_pedidos_nulos,
  COUNTIF(qt_material IS NULL) AS qt_material_nulos,
  COUNTIF(vlr_venda_desconto IS NULL) AS desconto_nulos,

  COUNTIF(
    des_canal_venda_final_agrup NOT IN ('App', 'Site')
    OR des_canal_venda_final_agrup IS NULL
  ) AS canal_fora_dominio,

  COUNTIF(nr_pedidos <= 0) AS nr_pedidos_nao_positivos,
  COUNTIF(qt_material <= 0) AS qt_material_nao_positivos,

  COUNTIF(receita_aprovada < 0) AS receita_aprovada_negativa,
  COUNTIF(receita_aprovada = 0) AS receita_aprovada_zero

FROM `{TABLE_ID}`
WHERE {DATE_FILTER}
