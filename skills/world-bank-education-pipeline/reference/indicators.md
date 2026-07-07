# Indicadores monitorados neste projeto

Todos os códigos abaixo são oficiais do World Bank
(https://data.worldbank.org) e correspondem exatamente às colunas
`indicator_code` do dataset `world_bank_intl_education` (Kaggle/BigQuery).

| Código | Nome | O que mede |
|---|---|---|
| `SE.XPD.TOTL.GD.ZS` | Gasto público em educação (% do PIB) | Quanto do PIB do país é destinado à educação — mede prioridade orçamentária em termos relativos à economia. |
| `SE.XPD.TOTL.GB.ZS` | Gasto público em educação (% do gasto público total) | Quanto do orçamento público total (não só do PIB) vai para educação — mede prioridade dentro do próprio governo. |
| `SE.PRM.ENRR` | Matrícula no ensino primário (% bruto) | Cobertura do ensino primário. Valores acima de 100% são comuns e esperados (refletem alunos fora da faixa etária ideal, repetência, etc.), não são erro de dado. |
| `SE.SEC.ENRR` | Matrícula no ensino secundário (% bruto) | Cobertura do ensino secundário, mesma lógica de "bruto" acima. |
| `SE.TER.ENRR` | Matrícula no ensino superior (% bruto) | Cobertura do ensino superior — indicador mais sensível a mudanças de política (ex: expansão de vagas), por isso costuma aparecer nos maiores crescimentos percentuais. |
| `SE.ADT.LITR.ZS` | Taxa de alfabetização de adultos (%) | % da população 15+ alfabetizada. Tende a saturar perto de 100% em países desenvolvidos — pouca margem de crescimento percentual restante nesses casos (não indica estagnação de política, apenas teto natural do indicador). |

## Indicadores mencionados no desafio, mas ainda não incluídos

O documento do desafio cita também **desempenho em avaliações
internacionais (PISA)** e **número de professores** como parte do dataset
EdStats. Esses ainda não estão no pipeline atual. Para adicionar (ex: PISA
como proxy de qualidade, complementando os indicadores de acesso/cobertura
que já temos):

- PISA não tem um código único simples no formato `SE.XXX` — os dados de
  PISA no World Bank aparecem sob códigos como `LO.PISA.MAT` (matemática),
  `LO.PISA.REA` (leitura), `LO.PISA.SCI` (ciências). Nem todos os países
  do nosso conjunto padrão participam do PISA (é uma avaliação por adesão).
- Professores: `SE.PRM.ENRL.TC.ZS` (proporção aluno/professor no primário)
  é um bom proxy de "número de professores" relativo à demanda.

Seguir o processo descrito em `SKILL.md` ("Como adicionar um novo
indicador") para incorporar qualquer um destes.
