# Agente Inteligente de Monitoramento Educacional 🌍📊

Pipeline completo que coleta indicadores educacionais do **World Bank**
(dataset público disponível no Kaggle), processa e enriquece os dados com
Python, gera **insights executivos com IA (Claude)** e orquestra todo o
fluxo com **n8n** — do gatilho ao relatório final salvo em disco.

> **Com pressa / vai gravar o vídeo agora?** Veja [`QUICKSTART.md`](QUICKSTART.md)
> e rode `python run_demo.py` — um único comando faz tudo (instala
> dependências, busca os dados, roda a análise e gera o relatório),
> nunca trava mesmo sem internet (cai para o dataset de amostra
> automaticamente) e imprime exatamente onde estão os resultados.

## Índice

- [Entrega do desafio — checklist](#entrega-do-desafio--checklist)
- [Contexto e objetivo](#contexto-e-objetivo)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Como configurar](#como-configurar)
- [Como rodar](#como-rodar)
- [Funcionalidades mínimas — checklist](#funcionalidades-mínimas--checklist)
- [Atividades Python](#atividades-python-mínimo-de-4-exigidas--projeto-cobre-7)
- [Skill do projeto](#skill-do-projeto)
- [Como o Claude Code foi utilizado](#como-o-claude-code-foi-utilizado)
- [Diferenciais (bônus)](#diferenciais-bônus--status-atual)
- [Créditos](#créditos)

---

## Entrega do desafio — checklist

| Exigido no desafio | Onde está |
|---|---|
| Link do GitHub | *(preencher após o push — ver seção "Publicar no GitHub" abaixo)* |
| Workflow do n8n exportado (`workflow.json`) | [`n8n/workflow.json`](n8n/workflow.json) (local) e [`n8n/workflow_cloud.json`](n8n/workflow_cloud.json) (100% n8n Cloud) |
| Código Python | [`src/`](src/) — ver [seção "Atividades Python"](#atividades-python-mínimo-de-4-exigidas--projeto-cobre-7) |
| README completo | este arquivo + [`n8n/README.md`](n8n/README.md), [`n8n/CLOUD_README.md`](n8n/CLOUD_README.md), [`QUICKSTART.md`](QUICKSTART.md) |
| Skills versionadas | [`skills/world-bank-education-pipeline/`](skills/world-bank-education-pipeline/) |
| Link do YouTube (vídeo 5-10 min) | *(preencher após gravar e publicar)* |



## Contexto e objetivo

Uma organização internacional quer acompanhar continuamente a evolução de
indicadores educacionais de diversos países para identificar tendências,
oportunidades e problemas. Este projeto implementa o Agente Inteligente de
Monitoramento Educacional que automatiza esse fluxo:

```
World Bank (API pública oficial / mesma fonte do dataset do Kaggle)
        │  src/fetch_worldbank_data.py
        ▼
  Python: limpeza, tratamento de ausentes,
  seleção de indicadores, agregações,
  rankings, cálculo de crescimento
        │
        ▼
  CSV final + resumo estruturado (JSON)
        │
        ▼
  IA (Claude): análise executiva real
  (não apenas resumo de números)
        │
        ▼
  n8n: orquestra tudo (gatilho → script →
  IA → armazenamento do relatório)
        │
        ▼
  Relatório executivo (.md) em reports/
```

---

## Estrutura do repositório

```
wb-edu-agent/
├── data/
│   ├── raw/                 # dados brutos (Kaggle) + dataset de amostra
│   └── processed/           # CSV final e resumo para IA (gerados pelo pipeline)
├── src/
│   ├── config.py            # caminhos, indicadores, parâmetros
│   ├── data_loader.py       # carregamento, limpeza, tratamento de ausentes
│   ├── indicators.py        # seleção de países/indicadores, formato wide
│   ├── analysis.py          # agregações, rankings, crescimento, comparação
│   ├── ai_report.py         # chamada à API do Claude, geração do relatório
│   ├── fetch_worldbank_data.py  # consulta real à API pública do World Bank
│   └── pipeline.py          # orquestra tudo (ponto de entrada do n8n)
├── tests/                   # testes unitários (pytest)
├── n8n/
│   ├── workflow.json        # workflow local (n8n chama o Python)
│   ├── workflow_cloud.json  # workflow 100% n8n Cloud (lógica em JS)
│   ├── README.md            # como importar e configurar (versão local)
│   └── CLOUD_README.md      # como importar e configurar (versão cloud)
├── skills/
│   └── world-bank-education-pipeline/
│       ├── SKILL.md         # Skill do projeto (ver seção "Skill" abaixo)
│       └── reference/indicators.md
├── prompts/
│   └── executive_report_prompt.md   # prompt versionado usado pela IA
├── notebooks/                # exploração e notebook original (Kaggle/BigQuery)
├── reports/                   # relatórios executivos gerados
├── requirements.txt
├── run_demo.py               # ponto de entrada único (instala, busca, analisa, relata)
└── README.md
```

---

## Como configurar

### 1. Ambiente Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Dados reais do World Bank

O pipeline consulta os dados nesta ordem de prioridade
(`src/data_loader.py::resolve_raw_data_path`):

1. **`data/raw/international_education.csv`** — dados reais. Duas formas de gerar este arquivo:
   - **Opção A (recomendada, automatizada, sem login)**: rodar
     `python -m src.fetch_worldbank_data`, que consulta diretamente a
     **API pública do World Bank** (mesma fonte primária do dataset do
     Kaggle) e já salva o CSV no schema correto. É essa chamada que o
     workflow do n8n executa automaticamente a cada disparo.
   - **Opção B (literal, dataset do Kaggle)**: baixar manualmente via
     `kaggle datasets download -d theworldbank/world-bank-intl-education`
     e salvar como `data/raw/international_education.csv`
     (instruções completas em [`data/raw/README.md`](data/raw/README.md)).
2. **`data/raw/sample_education_data.csv`** — fallback: dataset sintético
   incluso no repositório (10 países, 6 indicadores, 2010–2022, com
   valores ausentes propositais), usado **apenas** se nenhum dos arquivos
   reais acima existir. Serve para o pipeline rodar de ponta a ponta em
   ambientes sem acesso à internet (ex: avaliação automática, CI).

> **Nota de transparência**: o ambiente usado para gerar esta primeira
> versão do projeto não tinha acesso à internet para baixar o dataset do
> Kaggle nem para chamar a API do World Bank, por isso o pipeline foi
> validado com o dataset de amostra. O script `src/fetch_worldbank_data.py`
> foi escrito e testado sintaticamente, mas a chamada real à internet
> deve ser validada no seu ambiente (que tem acesso à rede) antes de
> considerar essa etapa "pronta" — rode-o localmente e confira o CSV
> gerado em `data/raw/international_education.csv`.

### 3. Chave da API do Claude

```bash
export ANTHROPIC_API_KEY="sua-chave-aqui"
# ou crie um arquivo .env com ANTHROPIC_API_KEY=sua-chave-aqui
```

---

## Como rodar

### Pipeline completo (Python)

```bash
# 1. Consultar os dados reais do World Bank (requer internet, sem login)
python -m src.fetch_worldbank_data

# 2. Rodar a limpeza, análise e geração do CSV final
python -m src.pipeline
# ou filtrando países/indicadores:
python -m src.pipeline --countries BRA USA CHN IND --indicators SE.TER.ENRR SE.XPD.TOTL.GD.ZS
```

Se você pular o passo 1, o pipeline usa automaticamente o dataset de
amostra incluso no repositório (ver seção "Dados reais do World Bank" acima).

Isso gera:
- `data/processed/final_report_data.csv` — dataset final consolidado (formato wide)
- `data/processed/growth_analysis.csv` — crescimento por país/indicador
- `data/processed/summary_for_ai.json` — resumo estruturado para a IA

### Gerar o relatório executivo com IA (sem n8n)

```bash
python -m src.ai_report
```

Gera `reports/executive_report.md` com a análise executiva completa (texto puro).

### Gerar a versão rica em HTML + PDF (com gráficos e cartões de KPI)

```bash
python -m src.export_pdf
```

Gera `reports/executive_report.html` e `reports/executive_report.pdf` —
versão com cabeçalho, cartões de KPI (período, maior crescimento, maior
queda, maior investimento), 4 gráficos de barra (crescimento, queda,
investimento, indicador absoluto) e 1 gráfico de dispersão
(investimento x resultado), todos gerados com matplotlib e embutidos no
HTML/PDF (arquivo autocontido, sem depender de imagens externas).
Requer `wkhtmltopdf` instalado no sistema (https://wkhtmltopdf.org/downloads.html).

### Orquestração completa via n8n

Ver [`n8n/README.md`](n8n/README.md) para importar `n8n/workflow.json`.
**Recomendado: rode o n8n localmente** (`npx n8n`, veja o guia) — o n8n
Cloud não tem acesso aos arquivos/Python do seu computador, então rodar
localmente é bem mais simples para este projeto e para o vídeo. Configure
a credencial da API do Claude.

> **Alternativa 100% na nuvem**: se preferir não depender do seu PC,
> veja [`n8n/CLOUD_README.md`](n8n/CLOUD_README.md) e importe
> `n8n/workflow_cloud.json` — é uma versão que reimplementa a análise em
> JavaScript, dentro de nós Code do próprio n8n, e roda inteiramente no
> n8n Cloud (a consulta ao World Bank, a limpeza e a análise não usam
> Python nesse caso — o Python continua sendo a "atividade Python"
> exigida no enunciado, feita em `src/*.py`).

O workflow cobre os
quatro elementos mínimos exigidos:

| Elemento              | Nó no n8n                                   |
|-----------------------|----------------------------------------------|
| Gatilho               | Schedule Trigger (semanal) + Manual Trigger  |
| Execução de script    | Execute Command → `python -m src.pipeline`   |
| Chamada para IA       | HTTP Request → API do Claude                  |
| Armazenamento         | Read/Write File → `reports/*.md`             |

### Testes

```bash
pytest tests/ -v
```

---

## Funcionalidades mínimas — checklist

- ✅ Selecionar países — `src/indicators.py::select_countries`
- ✅ Selecionar indicadores — `src/indicators.py::select_indicators`
- ✅ Comparar países — `src/analysis.py::compare_countries`
- ✅ Gerar ranking — `src/analysis.py::rank_countries_by_indicator`
- ✅ Gerar insights — `src/ai_report.py` (via API do Claude)
- ✅ Produzir relatório — `reports/executive_report.md`

## Atividades Python (mínimo de 4 exigidas — projeto cobre 7)

1. **Limpeza de dados** — `data_loader.clean_data` (duplicatas, tipos, remoção de agregados regionais)
2. **Tratamento de valores ausentes** — `data_loader.handle_missing_values` (interpolação linear por série)
3. **Seleção de indicadores/países** — `indicators.select_indicators`, `indicators.select_countries`
4. **Agregações** — `analysis.aggregate_by_country_indicator`
5. **Rankings** — `analysis.rank_countries_by_indicator`
6. **Cálculo de crescimento** (variação % e CAGR) — `analysis.calculate_growth`
7. **Comparação entre países** — `analysis.compare_countries`
8. **Geração de CSV final** — `pipeline.run_pipeline`

---

## Skill do projeto

Este projeto versiona uma **Skill** própria em
[`skills/world-bank-education-pipeline/SKILL.md`](skills/world-bank-education-pipeline/SKILL.md),
seguindo o mesmo formato usado pelas Skills do Claude (frontmatter com
`name`/`description` + instruções em Markdown).

Ela encapsula o conhecimento específico deste projeto que um agente
(Claude Code, Codex, ou qualquer pessoa nova no repositório) precisa para
trabalhar nele com segurança: o schema de dados, onde cada regra de
negócio vive **nas duas implementações paralelas** (Python e a versão
JavaScript usada pelo `workflow_cloud.json`), como adicionar um novo país
ou indicador sem quebrar a paridade entre as duas versões, armadilhas já
enfrentadas (ex: o bug do `groupby().apply()` no pandas 3.x, a ordem de
carregamento do `.env`), e as convenções do prompt usado pela IA.

Ideia por trás dela: qualquer extensão futura deste projeto (novo
indicador, novo país, nova regra de análise) deveria começar por essa
Skill, para não esquecer de replicar a mudança nos dois lados (Python e
JS) nem repetir bugs já resolvidos.

## Como o Claude Code foi utilizado

> Nota de transparência: o desenvolvimento foi feito em conversa direta com
> o Claude (interface de chat com execução de código), não a ferramenta de
> linha de comando "Claude Code" isoladamente. As tarefas realizadas são as
> mesmas que o enunciado lista como exemplo de uso do Claude Code/Codex —
> os exemplos abaixo são reais, tirados do histórico real de
> desenvolvimento deste projeto, não um template preenchido depois.

- **Criação de funções Python**: implementação de `calculate_growth`
  (variação % e CAGR por país/indicador com classificação automática de
  tendência "evoluiu"/"estagnado"/"regrediu"), `handle_missing_values`
  (interpolação linear por série com fallback de forward/backward-fill nas
  bordas), e `fetch_worldbank_data.py` (consulta paginada à API pública do
  World Bank com paridade de schema ao dataset do Kaggle).

- **Geração de testes**: testes unitários de `data_loader.py` e
  `analysis.py` cobrindo casos de borda reais (séries totalmente vazias,
  duplicatas, países agregados como "World", cálculo de CAGR com valores
  negativos). Como o ambiente de desenvolvimento não tinha acesso à
  internet para instalar o `pytest`, os mesmos testes foram também
  validados manualmente via `assert` antes da entrega, garantindo que a
  lógica está correta independentemente do ambiente de quem for rodar.

- **Identificação e correção de bugs reais** (não hipotéticos — apareceram
  durante o desenvolvimento):
  - `groupby(...).apply(...)` no pandas 3.x passou a excluir por padrão as
    colunas de agrupamento do resultado (`include_groups=False`), o que
    quebrava `handle_missing_values` silenciosamente. Corrigido trocando
    por `groupby(...).transform(...)`.
  - `run_demo.py` travava sem aviso ao instalar dependências em ambientes
    com pip "externally-managed" (comum em Ubuntu/Debian/WSL) — corrigido
    com detecção automática do erro e retry com `--break-system-packages`.
  - O carregamento do arquivo `.env` só acontecia dentro do subprocesso
    Python que rodava a IA, nunca no processo principal do `run_demo.py`
    — por isso a etapa de IA era sempre pulada mesmo com a chave
    configurada certinha. Corrigido chamando `load_dotenv()` explicitamente
    também no processo principal, antes da checagem da variável.
  - No workflow do n8n Cloud, o nó de anexo de e-mail falhava porque
    texto puro não é aceito como anexo — corrigido criando um nó Code que
    usa `this.helpers.prepareBinaryData()` para gerar um binário de
    verdade a partir do HTML do relatório.

- **Refatoração**: divisão do pipeline em módulos de responsabilidade única
  (`data_loader`, `indicators`, `analysis`, `ai_report`, `pipeline`,
  `fetch_worldbank_data`), e posteriormente **reimplementação completa da
  mesma lógica em JavaScript** (dentro dos nós Code do
  `workflow_cloud.json`) para permitir rodar 100% no n8n Cloud sem
  depender de Python local — mantendo o mesmo comportamento (limpeza,
  interpolação, agregações, rankings, cálculo de crescimento) nas duas
  linguagens.

- **Criação de scripts auxiliares**: `run_demo.py` (orquestrador único que
  instala dependências, busca dados, roda a análise e gera o relatório com
  tratamento de erro em cada etapa) e o gerador do dataset sintético de
  amostra (`data/raw/sample_education_data.csv`), usado como fallback
  quando não há internet ou dados reais disponíveis.

- **Documentação**: geração e revisão de todas as docstrings de `src/*.py`,
  do `README.md`, dos guias `QUICKSTART.md`, `n8n/README.md` e
  `n8n/CLOUD_README.md`, e da Skill do projeto (`skills/world-bank-education-pipeline/SKILL.md`).

---

## Diferenciais (bônus) — status atual

- ✅ **Gráficos automáticos**: implementado. Python via matplotlib
  (`src/report_builder.py`) e n8n Cloud via PNG gerado sob demanda pela
  API do QuickChart.io (nó "Montar Relatório HTML com Gráficos") — 4
  gráficos de barra + 1 de dispersão em cada versão. (Optamos por PNG em
  vez de SVG no n8n porque a maioria dos clientes de e-mail, Gmail
  incluso, não renderiza `<svg>` no corpo do e-mail.)
- ✅ **Exportação para PDF**: implementado via `python -m src.export_pdf`
  (usa `wkhtmltopdf` para converter o HTML rico em PDF, com os mesmos
  gráficos e cartões de KPI).
- ✅ **Agendamento periódico no n8n**: já configurado (Schedule Trigger
  semanal) em `n8n/workflow.json` e `n8n/workflow_cloud.json`.
- ⬜ **Dashboard / Streamlit**: ainda não implementado. `streamlit` já
  está em `requirements.txt`; a ideia é criar `app.py` reaproveitando
  `src.data_loader`, `src.indicators`, `src.analysis` e
  `src.report_builder` para montar um dashboard interativo de seleção de
  países/indicadores, com os mesmos gráficos e exportação em PDF.
- ⬜ **Alertas por limite**: ainda não implementado. Ideia: nó IF no n8n
  avaliando `summary_for_ai.json → top_decline` e disparando Slack/Email
  quando algum indicador cair além de um limite configurável.
- ⬜ **Bases complementares**: ainda não implementado. Ideia: enriquecer
  com dados de PIB per capita (World Bank `NY.GDP.PCAP.CD`) para
  relacionar investimento educacional a nível de riqueza do país.
- ✅ **Análises incomuns com base nos dados**: o gráfico de dispersão
  investimento x resultado (em ambas as versões) e a seção correspondente
  do prompt da IA já cobrem isso — mostra que quem mais investe nem
  sempre é quem mais cresce.

---

## Publicar no GitHub

Se ainda não subiu o projeto, os passos são:

```bash
cd wb-edu-agent
git init
git add .
git commit -m "Agente Inteligente de Monitoramento Educacional - Desafio Acelera AI"
```

Crie um repositório vazio no GitHub (https://github.com/new — **não**
marque "Add a README", já temos um) e depois:

```bash
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/NOME-DO-REPOSITORIO.git
git push -u origin main
```

Depois de publicado:
1. Copie o link do repositório e cole na tabela [Entrega do desafio](#entrega-do-desafio--checklist) acima.
2. Confira no próprio GitHub se `data/raw/international_education.csv` (dataset real, se você gerou um) não foi versionado sem querer — o `.gitignore` já bloqueia isso por padrão, mas vale checar (arquivos de dado real podem ser grandes).
3. Confira se `.env` **não** aparece no repositório (também já está no `.gitignore` — nunca suba sua chave da API).
4. Grave o vídeo (5-10 min, ver roteiro sugerido abaixo), publique no YouTube (pode ser "não listado") e cole o link na mesma tabela.

## Créditos

Baseado no notebook original *"How to Query the World Bank: Education
Data (BigQuery Dataset)"* (Kaggle), adaptado para um pipeline local
completo com Python + IA + n8n. Dataset: [World Bank: Education Data
(Kaggle)](https://www.kaggle.com/datasets/theworldbank/world-bank-intl-education).
