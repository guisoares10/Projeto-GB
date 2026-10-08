-- case projeto GB
-- 32_sql_negative_sign.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 2.4.7 É erro de sinal? E o desconto explica alguma coisa?
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID

SELECT
  COUNTIF(receita_aprovada < 0) AS linhas_negativas,
  COUNTIF(receita_aprovada < 0 AND qt_material > 0) AS negativas_com_qt_positiva,
  COUNTIF(receita_aprovada < 0 AND nr_pedidos > 0) AS negativas_com_pedidos_positivos,
  COUNTIF(receita_aprovada < 0 AND vlr_venda_desconto < 0) AS negativas_com_desconto_negativo,
  COUNTIF(receita_aprovada < 0 AND receita_aprovada + vlr_venda_desconto <= 0) AS negativas_com_preco_cheio_nao_positivo
FROM `{TABLE_ID}`
WHERE {DATE_FILTER}
