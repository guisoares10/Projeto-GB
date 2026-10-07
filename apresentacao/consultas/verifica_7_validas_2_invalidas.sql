WITH slots AS (
  SELECT
    dt_hr_venda,
    des_canal_venda_final_agrup,
    COUNTIF(NOT REGEXP_CONTAINS(des_categoria_material, r'^[0-9.,]+$')) AS categorias_validas,
    COUNTIF(REGEXP_CONTAINS(des_categoria_material, r'^[0-9.,]+$'))     AS categorias_invalidas,
    SUM(IF(REGEXP_CONTAINS(des_categoria_material, r'^[0-9.,]+$'), qt_material, 0)) AS qt_invalida
  FROM `gms-prod-01.projeto_gb.fact_vendas`
  GROUP BY 1, 2
)
SELECT *
FROM slots
WHERE categorias_validas = 7
  AND categorias_invalidas >= 2
ORDER BY dt_hr_venda, des_canal_venda_final_agrup
