# Contexto para o Claude

Case técnico do processo de Especialista de Dados (Grupo Boticário). Avaliação de ML ponta a ponta:
1. Observabilidade/data quality das entradas (limites, alertas, outliers que atrapalham o modelo)
2. Organização do modelo
3. Automação da verificação de resultados

Problema: **previsão de vendas**. Dados ainda não recebidos -> tudo genérico e guiado por config.
Stack: Python, GCP (BigQuery, BigQuery Studio notebooks / Colab Enterprise). Resultados de cada
execução gravados em tabelas BigQuery (com id_execucao, timestamp, versão do código) para inspeção
via `%%bigquery` / bigframes.

## Diretrizes
- Idioma da documentação, comentários e mensagens: português.
- Nunca versionar dados (ver .gitignore).
- Código como pacote instalável (`src/gb_ml`); notebooks finos apenas chamam o pacote.
- Data quality: severidade warn/error; erro crítico bloqueia treino (gate).
- Checagens planejadas: schema/tipos, grão único, nulos, limites de negócio, outliers robustos
  (IQR/MAD), buracos de datas, datas futuras, freshness, volume de linhas, drift (PSI).
- Forecast: baseline obrigatório (naive sazonal / média móvel), LightGBM, backtest com janela
  expansível por horizonte, métricas WAPE/MAE/bias/skill vs baseline, quality gate.
- Testes com pytest.
