# Projeto GB — ML ponta a ponta (previsão de vendas)

Preparação para o case técnico de Especialista de Dados: um pipeline de Machine Learning
de ponta a ponta, do **controle de qualidade das entradas** até a **automação da verificação
dos resultados**.

## Objetivos do case (conforme alinhado com a liderança)
1. **Observabilidade e data quality** das tabelas de entrada: checar se os valores fazem
   sentido, com limites e alertas para números fora da realidade que possam atrapalhar o modelo.
2. **Organização do modelo**: código modular, versionado, reprodutível.
3. **Automação** da verificação dos resultados (backtest, métricas, gates).

Os dados ainda não foram recebidos. Por isso a camada de data quality é **genérica**
(funciona com qualquer tabela via configuração) e a modelagem é um esqueleto de forecast
pronto para receber os dados.

## Estrutura
```
src/gb_ml/
  io/          leitura/escrita (arquivo local e BigQuery)
  profiling/   perfil automático de qualquer tabela
  dq/          checagens genéricas de qualidade + severidade + gate
  features/    features de série temporal (lags, calendário)
  model/       baseline, treino, backtest, métricas
configs/tabelas/  um YAML por tabela descrevendo o contrato de dados
notebooks/        notebooks finos (BigQuery Studio) que só chamam o pacote
tests/
data/             dados locais (ignorado pelo git)
```

## Instalação
```bash
pip install -e ".[bq,ml,dev]"
```

No notebook do BigQuery Studio:
```python
!pip install "git+https://github.com/guisoares10/Projeto-GB---ML.git#egg=gb-ml[bq,ml]"
```

> Os dados do case **nunca** são versionados neste repositório.
