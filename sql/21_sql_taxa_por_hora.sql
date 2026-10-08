-- 21_sql_taxa_por_hora.sql
-- Usada no notebook analise_exploratoria.ipynb, seção: 2.3.4 Existe padrão por hora do dia?
-- Parâmetros preenchidos por carregar_sql(): DATE_FILTER, TABLE_ID, condicao_sql

    SELECT
      EXTRACT(HOUR FROM dt_hr_venda) AS hora,
      COUNT(*) AS linhas,
      COUNTIF({condicao_sql}) AS ocorrencias
    FROM `{TABLE_ID}`
    WHERE {DATE_FILTER}
    GROUP BY 1
    ORDER BY 1
    
