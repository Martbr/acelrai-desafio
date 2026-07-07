---
name: world-bank-education-pipeline
description: Use this skill whenever working on the World Bank Education Monitoring pipeline in this repository — adding/removing countries or indicators, changing the data cleaning or analysis logic (src/data_loader.py, indicators.py, analysis.py, pipeline.py), editing the AI executive-report prompt, or updating either n8n workflow (local Python-based or 100% n8n Cloud JavaScript-based). It encodes the project's data schema, known pitfalls, and conventions so that changes stay consistent across the Python pipeline AND its JavaScript reimplementation used by the n8n Cloud workflow.
---

# World Bank Education Pipeline — Skill

Este projeto tem **duas implementações paralelas da mesma lógica**:

1. **Python** (`src/*.py`) — roda localmente ou via n8n local (Execute Command).
2. **JavaScript** (dentro dos nós "Code" de `n8n/workflow_cloud.json`) — roda 100%
   dentro do n8n Cloud, sem Python.

Qualquer mudança de regra de negócio (novo indicador, nova forma de calcular
crescimento, novo critério de estagnação, etc.) precisa ser replicada **nos
dois lugares**, ou as duas versões do projeto vão divergir silenciosamente.
Esse é o cuidado #1 ao usar esta skill.

## Schema de dados (não mudar sem atualizar os dois lados)

Toda linha de dado, em qualquer estágio do pipeline, segue este formato
(idêntico ao dataset do Kaggle / BigQuery `world_bank_intl_education`):

```
country_name    (string)  ex: "Brazil"
country_code    (string)  ISO3, ex: "BRA"
indicator_code  (string)  código oficial do World Bank, ex: "SE.PRM.ENRR"
indicator_name  (string)  nome legível do indicador
year            (int)
value           (float | null)
```

## Onde cada coisa vive

| Conceito | Python | JavaScript (n8n Cloud) |
|---|---|---|
| Lista de países | `src/config.py` → `DEFAULT_COUNTRIES` (em `fetch_worldbank_data.py`) | Nó "Consultar World Bank + Analisar" → constante `COUNTRIES` |
| Lista de indicadores | `src/config.py` → `INDICATORS_OF_INTEREST` | Mesmo nó → constante `INDICATORS` |
| Limpeza + valores ausentes | `src/data_loader.py` (`clean_data`, `handle_missing_values`, interpolação linear via `groupby(...).transform(...)`) | Mesmo nó → `cleanAndFillMissing` + `interpolateGroup` (grade de anos completa + interpolação linear manual) |
| Agregações / rankings / crescimento | `src/analysis.py` | Mesmo nó → `aggregateByCountryIndicator`, `rankCountriesByIndicator`, `calculateGrowth` |
| Prompt da IA (system + user) | `src/ai_report.py` + `prompts/executive_report_prompt.md` | Nó "Montar Prompt para a IA" (mesmo texto, mantido manualmente em sincronia) |
| Relatório rico (KPIs + gráficos + HTML) | `src/report_builder.py` (matplotlib, embutido em base64) | Nó "Montar Relatório HTML com Gráficos" (PNG via QuickChart.io — ver nota abaixo) |
| Exportação em PDF | `src/export_pdf.py` (wkhtmltopdf) | Não existe nativamente — usar "imprimir como PDF" a partir do e-mail/HTML recebido |

**Regra prática**: ao editar o prompt da IA em um lugar, copie a mudança para
o outro (`prompts/executive_report_prompt.md`, `src/ai_report.py` e o nó
"Montar Prompt para a IA" do `workflow_cloud.json`) na mesma tarefa. O
mesmo vale para os gráficos do relatório: `src/report_builder.py` e o nó
"Montar Relatório HTML com Gráficos" devem gerar os mesmos 4 gráficos de
barra (crescimento, queda, investimento, indicador absoluto) + 1 gráfico
de dispersão (investimento x resultado) — ambos como PNG de verdade
(matplotlib em Python, QuickChart.io em JS), nunca SVG puro (não
renderiza em e-mail).

## Como adicionar um novo país

1. Python: adicione o código ISO3 em `DEFAULT_COUNTRIES` (`src/fetch_worldbank_data.py`).
2. JavaScript: adicione o mesmo código em `COUNTRIES` no nó "Consultar World
   Bank + Analisar" do `workflow_cloud.json`.
3. Rode `python -m src.pipeline` localmente para conferir que o país aparece
   em `data/processed/final_report_data.csv` antes de mexer no n8n.

## Como adicionar um novo indicador

1. Confirme o código oficial do indicador em https://data.worldbank.org
   (formato `XX.YYYY.ZZZZ`, ex: `SE.PRM.CMPT.ZS`).
2. Python: adicione `"CÓDIGO": "Nome legível em português"` em
   `INDICATORS_OF_INTEREST` (`src/config.py`).
3. JavaScript: adicione a mesma entrada em `INDICATORS` no nó "Consultar
   World Bank + Analisar".
4. Se o indicador tiver uma faixa de valores muito diferente dos demais
   (ex: número absoluto de professores, em vez de percentual), verifique se
   `classify_trend`/`classifyTrend` (limiar de 3% para "estagnado") ainda
   faz sentido para ele — pode precisar de um limiar próprio.

## Armadilhas conhecidas (já enfrentadas neste projeto)

- **pandas 3.x**: `DataFrameGroupBy.apply()` passou a excluir por padrão as
  colunas de agrupamento do resultado (`include_groups=False`). Isso já
  quebrou `handle_missing_values` uma vez. Prefira
  `groupby(...).transform(...)` a `groupby(...).apply(...)` quando as
  colunas de agrupamento precisam continuar no resultado.
- **Windows**: `python3` geralmente não existe no PATH (só `python`). Nós
  do n8n local (`workflow.json`) e instruções para o usuário devem usar
  `python`, não `python3`. `sys.executable` dentro de scripts Python (como
  `run_demo.py`) evita esse problema.
- **`.env` só é carregado se algo já tiver importado `src.config`** (é lá
  que o `load_dotenv()` roda). Qualquer script/entry-point novo que precise
  de `ANTHROPIC_API_KEY` deve garantir que `src.config` (ou um
  `load_dotenv()` equivalente) rode antes de checar `os.environ`.
- **n8n Cloud não acessa o computador local**: o nó "Execute Command" só
  funciona se o n8n estiver rodando na mesma máquina que tem os arquivos do
  projeto (n8n local via `npx n8n`/`n8n start`). Para n8n Cloud de verdade,
  use sempre a versão 100% JavaScript (`workflow_cloud.json`).
- **Anexos de e-mail no n8n exigem dado binário**, não texto. Use
  `this.helpers.prepareBinaryData(buffer, fileName, mimeType)` dentro de um
  nó Code para converter texto em anexo real (ver nó "Preparar Anexo do
  Relatório").
- **Gráficos em `<svg>` não aparecem no corpo de e-mails** (Gmail e a
  maioria dos clientes bloqueiam SVG embutido por segurança). O nó
  "Montar Relatório HTML com Gráficos" usa PNG de verdade via
  QuickChart.io (`POST https://quickchart.io/chart/create`, gratuito,
  sem chave para uso moderado — limite de 60 gráficos/min) em vez de
  desenhar SVG manualmente. Se recriar esse nó do zero, não volte para
  SVG achando que é mais simples — funciona no navegador mas não no
  e-mail.

## Convenções de prompt para o relatório executivo da IA

O prompt (em `prompts/executive_report_prompt.md`, replicado em
`src/ai_report.py` e no nó "Montar Prompt para a IA") segue estas regras
fixas — mudanças devem preservar a intenção:

1. A IA nunca deve só resumir números — sempre hipótese causal +
   implicação prática.
2. Deve nomear explicitamente: quem mais evoluiu, quem estagnou/regrediu,
   quem mais investe, melhores indicadores absolutos.
3. Hipóteses causais devem ser marcadas como hipótese, não fato.
4. Termina sempre com recomendações priorizadas e acionáveis.
5. O dado enviado à IA é sempre um **resumo pré-calculado** (rankings,
   crescimento, agregações), nunca o dataset bruto inteiro — economiza
   contexto e evita que a IA vire uma calculadora em vez de analista.

## Testando mudanças antes de subir para o n8n

Este projeto tem o hábito de testar a lógica em isolamento antes de colar
em qualquer nó do n8n (o n8n não tem depurador fácil de usar). Para
JavaScript: escreva um teste standalone com Node.js puro (`node
arquivo_de_teste.js`), mockando `this.helpers.httpRequest` quando precisar
simular a API do World Bank, e só depois cole o código validado no nó
Code correspondente. Para Python: `pytest tests/ -v` (ou testes manuais com
`assert`, se o pytest não estiver disponível no ambiente).

## Arquivos de referência

- `reference/indicators.md` — lista completa dos indicadores atualmente
  monitorados, com o significado de cada um.
