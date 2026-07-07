# Rodando 100% no n8n Cloud (sem Python local)

Este é um **segundo workflow** (`workflow_cloud.json`), separado do
`workflow.json` original. A diferença:

| | `workflow.json` (original) | `workflow_cloud.json` (este) |
|---|---|---|
| Onde roda a análise | Python, no seu computador | JavaScript, dentro do próprio n8n Cloud |
| Precisa do seu PC ligado? | Sim (nó Execute Command chama seu Python) | **Não** |
| Precisa importar dados/arquivos? | Sim (o projeto Python inteiro) | **Não** — é só importar 1 arquivo JSON |
| Cobre as atividades Python obrigatórias do enunciado? | Sim, em `src/*.py` | Não — a lógica equivalente está em JavaScript, dentro do n8n. Para a entrega, mantenha o `src/*.py` como a "atividade Python" e use este workflow como a versão "tudo na nuvem" |

Ou seja: **isso não substitui a parte Python do seu projeto** (o enunciado
pede Python explicitamente) — é uma forma alternativa e 100% online de
rodar o mesmo tipo de fluxo, útil para o vídeo caso o Python local
continue dando trabalho, ou como demonstração extra de que o mesmo
raciocínio pode rodar de duas formas diferentes.

## O que você precisa subir/configurar

Só **um arquivo**: `n8n/workflow_cloud.json`. Não precisa subir nenhum
outro arquivo do projeto — toda a lógica (consulta ao World Bank,
limpeza, interpolação de valores ausentes, agregações, rankings,
cálculo de crescimento/CAGR, e o prompt da IA) já está dentro dos nós
"Code" do próprio workflow, em JavaScript.

## Passo a passo

### 1. Importe o workflow

No n8n Cloud: menu **☰ > Import from File** e selecione
`n8n/workflow_cloud.json`. (Se preferir, `Import from URL` também
funciona se você hospedar o arquivo em algum lugar, ex: um Gist do
GitHub.)

### 2. Configure a credencial da API do Claude

**Credentials > New > Header Auth**:
- Nome do header: `x-api-key`
- Valor: sua `ANTHROPIC_API_KEY`

No nó **"Chamar API do Claude (análise executiva)"**, clique nele, vá em
**Authentication > Generic Credential Type > Header Auth** e selecione a
credencial criada.

### 3. Configurando o envio pelo nó do Gmail

Você já trocou o nó de e-mail pelo **Gmail** nativo do n8n (ótima escolha
— evita precisar de servidor SMTP, usa OAuth2 com sua própria conta
Google). O motivo do e-mail ter chegado vazio quase certamente foi isso:
ao trocar de um tipo de nó para outro, o n8n **não migra os campos
automaticamente** — então "Assunto" e "Corpo" provavelmente ficaram em
branco na troca.

Depois de importar o `workflow_cloud.json` atualizado, você vai ver um
novo nó chamado **"Preparar Anexo do Relatório"** logo antes de onde
estava o nó de e-mail. Conecte a saída dele ao SEU nó do Gmail (arraste
a seta) e configure o nó do Gmail assim:

| Campo                     | Valor                                                    |
|----------------------------|-----------------------------------------------------------|
| Resource                  | `Message`                                                  |
| Operation                 | `Send`                                                     |
| To                        | seu e-mail (ex: `voce@gmail.com`)                          |
| Subject                   | `Relatório Executivo - Indicadores Educacionais` (ou uma expressão: `={{$json.fileName}}`) |
| Email Type                | `HTML`                                                     |
| Message                   | **`={{ $json.htmlContent }}`** ← provavelmente este campo ficou vazio |
| Options > Attachments     | Add Attachment → **Input Data Field Name**: `report`       |

O ponto mais importante é o campo **Message**: clique nele, ative o modo
"Expression" (o ícone `fx` ao lado do campo) e digite exatamente:
```
{{ $json.htmlContent }}
```
Sem isso, o corpo do e-mail realmente sai vazio, mesmo com tudo mais
certo.

Para o **anexo**: em "Options", procure "Attachments" (ou
"Add Attachment"), e no campo que pede o nome da propriedade binária,
digite `report` — é exatamente o nome que o nó "Preparar Anexo do
Relatório" usa ao criar o arquivo.

Se sua conta do Gmail no n8n ainda não estiver conectada, o próprio n8n
vai pedir para você fazer login com sua conta Google na primeira vez que
configurar a credencial — é só seguir o fluxo de autorização que aparece.

### 4. Rode

Clique no nó **"Executar Manualmente (teste)"** e depois em **"Execute
workflow"**. Acompanhe os nós ficando verdes:

1. **Consultar World Bank + Analisar** — 10 a 40 segundos.
2. **Montar Prompt para a IA** — instantâneo.
3. **Chamar API do Claude** — alguns segundos.
4. **Extrair Relatório da Resposta** — instantâneo.
5. **Montar Relatório HTML com Gráficos** — instantâneo (gera os
   gráficos de barra em SVG e converte o texto da IA para HTML).
6. **Preparar Anexo do Relatório** — instantâneo (transforma o HTML em
   anexo binário de verdade).
7. **Seu nó do Gmail** — alguns segundos, envia o e-mail com o corpo em
   HTML e o relatório também em anexo.

Se tudo der certo, o e-mail chega com o relatório formatado e os três
gráficos (maior crescimento, maior queda, maior investimento).

### 5. Sobre o PDF

O n8n não tem um conversor nativo de HTML para PDF sem depender de um
serviço externo (ex: PDFShift, api2pdf — exigem cadastro e chave de API
próprios). Como o e-mail já chega com o HTML formatado e com gráficos,
o caminho mais simples para ter um PDF é:
- Abrir o e-mail (ou o arquivo `.html` — veja nota abaixo) no navegador
  e usar **Ctrl+P > Salvar como PDF**. Leva 5 segundos e fica
  idêntico ao que você vê na tela.
- Se quiser 100% automático, dá para adicionar um nó **HTTP Request**
  chamando uma dessas APIs de conversão depois do nó "Montar Relatório
  HTML com Gráficos" — me avise se quiser que eu monte esse nó
  específico (só preciso saber qual serviço você prefere usar).

> Se quiser também salvar uma cópia em arquivo (além do e-mail), veja a
> seção "Sobre gerar arquivo" mais abaixo.

## Sobre os gráficos (PNG via QuickChart, não mais SVG)

Se você importou uma versão anterior deste workflow, os gráficos vinham
em `<svg>` — e por isso não apareciam no corpo do e-mail (Gmail e a
maioria dos clientes bloqueiam SVG embutido, por segurança). A versão
atual gera os gráficos como **imagens PNG de verdade**, usando a API
gratuita do [QuickChart.io](https://quickchart.io) (não exige conta nem
chave para este volume de uso — limite gratuito de 60 gráficos/min,
usamos só 5 por execução).

Dois detalhes práticos:
- **Seu cliente de e-mail pode pedir para "mostrar imagens"** na primeira
  vez que abrir o e-mail — isso é normal para qualquer imagem remota
  (não é specific deste projeto), é só clicar em "mostrar imagens" ou
  "confiar no remetente".
- Se o QuickChart estiver temporariamente indisponível, o gráfico daquele
  trecho é substituído por um texto avisando isso — o resto do relatório
  continua normalmente, o workflow não quebra por causa disso.

## Ativar o agendamento semanal

Se quiser que rode sozinho toda semana, ative o toggle **"Active"** no
canto superior direito. Diferente da versão local, isso funciona mesmo
com seu computador desligado, porque tudo roda dentro do n8n Cloud.

## Sobre gerar arquivo (opcional, além do e-mail)

nó "Read/Write File" (usado numa versão anterior) exige que o dado de
entrada seja **binário**, não texto — por isso deu o erro que você viu
antes. Boa notícia: o novo nó "Preparar Anexo do Relatório" já resolve
isso (gera o binário certinho, na propriedade `report`). Se quiser
também salvar em arquivo além de mandar por e-mail, conecte um nó
**Read/Write File** (operação "Write File to Disk", Input Binary Field =
`report`) na saída de "Preparar Anexo do Relatório", em paralelo ao seu
nó do Gmail.

## Limitações desta versão (para você saber o que dizer no vídeo)

- A consulta ao World Bank é feita direto pela API pública (mesma fonte
  do dataset do Kaggle), sem passar pelo arquivo CSV do Kaggle em si —
  isso é intencional, já que o n8n Cloud não tem onde guardar/ler esse
  CSV localmente.
- Os 10 países e 6 indicadores estão fixos no código do nó "Consultar
  World Bank + Analisar" (constantes `COUNTRIES` e `INDICATORS` no topo
  do script). Para mudar, edite direto o código dentro do nó no n8n.
- Esta versão não gera o CSV final como arquivo baixável por padrão — ele
  fica disponível no campo `finalCsv` do primeiro nó Code (você pode
  clicar nele e copiar, ou adicionar outro nó de storage para salvá-lo
  também).
