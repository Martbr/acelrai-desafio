# Workflow n8n — Agente de Monitoramento Educacional

## ⚠️ Importante: n8n Cloud x n8n local

O nó **"Execute Command"** roda o comando no servidor onde o n8n está
instalado. Se você usa **n8n Cloud**, esse servidor é da infraestrutura do
n8n na nuvem — ele **não tem acesso** aos arquivos nem ao Python instalado
no seu computador Windows. Por isso, para este projeto, **rodar o n8n
localmente é o caminho recomendado** (e muito mais simples para gravar o
vídeo).

## Como rodar o n8n localmente no Windows

Requer apenas o **Node.js** instalado (https://nodejs.org, versão LTS).

1. Abra o terminal (cmd ou PowerShell) e rode:
   ```
   npx n8n
   ```
   Na primeira vez, ele vai baixar o n8n (pode demorar um pouco). Quando
   terminar, vai aparecer algo como:
   ```
   Editor is now accessible via:
   http://localhost:5678
   ```
2. Abra esse endereço no navegador. Crie uma conta local (é só local, não
   precisa de internet para isso, fica só na sua máquina).
3. Deixe esse terminal aberto — é o "servidor" do n8n rodando. Para
   encerrar depois, feche o terminal ou `Ctrl+C`.

> Alternativa: se preferir não usar `npx` toda vez, pode instalar de vez
> com `npm install -g n8n` e depois só rodar `n8n` no terminal.

## Estrutura do fluxo

```
[Agendamento Semanal] ─┐
                        ├─> Consultar World Bank + Rodar Pipeline
[Executar Manualmente]─┘         (fetch + limpeza + análise)
                                            │
                                            v
                                Ler summary_for_ai.json
                                            │
                                            v
                                Montar Prompt para a IA
                                            │
                                            v
                        Chamar API do Claude (análise executiva)
                                            │
                                            v
                          Extrair Relatório da Resposta
                                            │
                                            v
                          Salvar Relatório em reports/
```

Isso cobre os quatro elementos mínimos exigidos: **gatilho** (agendamento
ou manual), **execução de script** (pipeline Python), **chamada para IA**
(API do Claude) e **armazenamento do resultado** (arquivo `.md` em
`reports/`).

## Passo a passo para importar e configurar

### 1. Importar o workflow

No n8n (local, `http://localhost:5678`): menu **☰ > Import from File**
(ou `Ctrl+O`) e selecione `n8n/workflow.json`.

### 2. Configurar o caminho do projeto (PROJECT_PATH)

O comando do nó "Consultar World Bank + Rodar Pipeline" precisa saber
onde está a pasta do projeto no seu PC. Duas formas de configurar:

**Opção A — variável de ambiente (recomendado):**
Antes de rodar `npx n8n`, defina no mesmo terminal:
```
set PROJECT_PATH=C:\Users\Bruno\Desktop\Aceleradoras\IA\Entrega\wb-edu-agent
npx n8n
```
(troque pelo caminho real da sua pasta — sem barra `\` no final)

**Opção B — editar direto no nó:**
Abra o nó "Consultar World Bank + Rodar Pipeline" no n8n e troque o
trecho `C:\caminho\para\wb-edu-agent` pelo caminho real da sua pasta,
tanto nesse nó quanto nos nós "Ler summary_for_ai.json" e "Salvar
Relatório em reports/".

### 3. Criar a credencial da API do Claude

No menu **Credentials > New > Header Auth**, crie uma credencial com:
- Nome do header: `x-api-key`
- Valor: sua `ANTHROPIC_API_KEY` (a mesma que você já usa no `.env`)

No nó **"Chamar API do Claude (análise executiva)"**, em Authentication,
selecione essa credencial.

### 4. Testar

Clique no nó **"Executar Manualmente (teste)"** e depois no botão
**"Execute workflow"** (ou "Test workflow") no topo da tela. Acompanhe
cada nó ficando verde (sucesso) ou vermelho (erro, com detalhes ao
clicar nele).

### 5. Ativar o agendamento (opcional)

Se quiser que rode sozinho semanalmente, ative o toggle **"Active"** no
canto superior direito do workflow. Isso só funciona enquanto o terminal
do `npx n8n` estiver aberto e rodando.

## Erros comuns

| Sintoma                                              | Causa provável                                                    |
|-------------------------------------------------------|--------------------------------------------------------------------|
| Nó "Execute Command" falha com "command not found"    | `python` não está no PATH do Windows, ou caminho do projeto errado |
| Nó "Ler summary_for_ai.json" não encontra o arquivo   | O pipeline não rodou com sucesso antes, ou PROJECT_PATH está errado |
| Nó "Chamar API do Claude" retorna 401                  | Credencial Header Auth com header/chave errados                    |
| Tudo roda mas o `.md` final vem vazio                  | Confira se o modelo em "Montar Prompt para a IA" (`claude-sonnet-4-6`) está correto/ativo na sua conta |

## Personalizações sugeridas (bônus)

- Trocar o nó final por **Slack** ou **Gmail** para notificar a equipe
  quando o relatório for gerado.
- Adicionar um nó **IF** após "Extrair Relatório da Resposta" para
  disparar um alerta quando algum indicador de `top_decline` no resumo
  ultrapassar um limite de queda definido.
- Adicionar um nó **Google Sheets** para registrar cada execução como
  uma nova linha em uma planilha de histórico.

## E se eu realmente precisar usar o n8n Cloud?

É possível, mas exige um passo a mais: como o n8n Cloud não acessa seu
PC, você precisaria expor sua máquina para a internet (ex: com
`ngrok`) e trocar o nó "Execute Command" por um nó **HTTP Request**
apontando para um pequeno servidor local (ex: Flask) que rode o
pipeline e devolva o JSON. Para o vídeo da disciplina, isso é
desnecessariamente complexo — rodar o n8n localmente (como descrito
acima) entrega o mesmo resultado de forma muito mais simples.
