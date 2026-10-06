# Case Técnico — Especialista de Dados I

Solução do case técnico para a posição de Especialista de Dados, organizada em duas frentes:
**Análise/Modelagem Preditiva** e **Inovação/Arquitetura de IA**.

## Seção 1 — Análise de Dados e Modelagem Preditiva

### Contexto
O arquivo entregue contém histórico de vendas do E-commerce entre **01/11/2025 e 30/06/2026**,
agregado por hora, categoria e canal.

Campos:
- `dt_hr_venda`
- `DES_CANAL_VENDA_FINAL_AGRUP`
- `DES_CATEGORIA_MATERIAL`
- `receita_aprovada`
- `nr_pedidos`
- `qt_material`
- `vlr_venda_desconto`

### Objetivos
1. Realizar EDA com análises objetivas e subjetivas.
2. Estudar preço médio de venda.
3. Avaliar potencial de vendas por dia da semana.
4. Entender flutuações de comportamento ao longo do dia.
5. Construir uma previsão diária e explicar:
   - escolha do(s) algoritmo(s);
   - estratégia de construção e validação;
   - variáveis/features mais importantes.

### Decisão analítica inicial
A EDA usa `qt_material` como proxy principal de **demanda operacional em unidades** e
`receita_aprovada` como KPI financeiro central. A etapa de modelagem documentará
explicitamente a escolha do target e poderá comparar as duas visões.


## Estratégia de EDA: BigQuery-first

A análise exploratória segue uma divisão intencional de responsabilidades:

```
BigQuery / SQL
    ↓
Data Quality, filtros, regras, agregações e redução de volume
    ↓
Pandas / Python
    ↓
estatística, visualização, interpretação e Machine Learning
```

Exemplos executados diretamente no BigQuery:
- nulos e domínios inválidos;
- duplicidade no grão hora × canal × categoria;
- identificação de categorias corrompidas com `SAFE_CAST`;
- receita negativa;
- cobertura temporal;
- agregação diária;
- thresholds de outlier por IQR;
- preço médio ponderado;
- potencial por dia da semana;
- perfil intradiário e dia da semana × hora.

Antes das consultas, o notebook faz `dry-run` para exibir uma estimativa dos bytes
processados. Isso mantém explícita a preocupação com custo e performance no BigQuery.

O Pandas recebe prioritariamente resultados agregados — por exemplo, a série diária —
em vez de reproduzir no notebook operações que pertencem ao data warehouse.

## Seção 2 — Inovação e Arquitetura de IA

Business case sobre análise de imagens/banners do site:
- condução do problema com um time sem conhecimento de programação;
- alternativa técnica usando modelos de IA/embeddings para imagens;
- arquitetura explicável para gestão sênior;
- MVP com avaliação de **Custo vs Retorno**;
- respeito ao processo de homologação/governança de ferramentas.

Essa seção será estruturada após a conclusão da modelagem da Seção 1.

## Entregáveis

- Código/notebooks hospedados neste GitHub.
- Apresentação executiva de aproximadamente **45 minutos**.
- A apresentação deve cobrir:
  - EDA e insights;
  - construção/validação do modelo;
  - proposta de IA da Seção 2;
  - impacto e valor em linguagem acessível para audiência não técnica.

## Estrutura

```
notebooks/
  01_eda_data_quality.ipynb       EDA específica do case
src/gb_ml/
  case_espec_i.py                 preparação e agregações específicas do arquivo
  dq/                             checks auxiliares
  profiling/                      utilitários de profiling/visualização
  model/                          modelagem (próxima etapa)
tests/
data/                              dados locais — não versionados
```

## Dados

A análise lê diretamente a tabela curada do BigQuery:

```
gms-prod-01.projeto_gb.fact_vendas
```

A carga original é preservada em:

```
gms-prod-01.projeto_gb.stg_fact_vendas
```

A tabela tratada `fact_vendas` é gerada a partir dela, com `ROUND` nos campos
monetários. As consultas usadas na análise ficam em `sql/`, numeradas na ordem
de uso no notebook (`01_sql_overview.sql`, `02_sql_daily.sql`, ...).

Os dados do case **não são versionados no repositório**.

## Instalação

```bash
python -m venv .venv
source .venv/Scripts/activate   # Git Bash no Windows
python -m pip install -e ".[bq,ml,dev]"
```

Para executar os testes:

```bash
pytest -v
```


## Autenticação local no BigQuery

No computador de desenvolvimento, o notebook utiliza Application Default Credentials.
Após instalar o Google Cloud CLI, autentique uma vez com:

```bash
gcloud auth application-default login
gcloud config set project gms-prod-01
```

O notebook então acessa diretamente `gms-prod-01.projeto_gb.fact_vendas`.
