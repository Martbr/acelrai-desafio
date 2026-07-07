# Início Rápido (para gravar o vídeo sem dor de cabeça)

Este guia assume que você não quer perder tempo debugando ambiente.
Existe **um único comando** para rodar tudo: `run_demo.py`.

## Passo 0 — Verifique se o Python está instalado

Abra o terminal (Prompt de Comando/PowerShell no Windows, Terminal no
Mac/Linux) e rode:

```bash
python3 --version
```

Se der erro "comando não encontrado", tente:

```bash
python --version
```

- Se nenhum dos dois funcionar, instale o Python em https://www.python.org/downloads/
  (marque a opção "Add Python to PATH" durante a instalação no Windows).
- Precisa de Python 3.9 ou mais recente.

> A partir daqui, troque `python3` por `python` nos comandos abaixo se foi
> esse o que funcionou para você no Passo 0.

## Passo 1 — Baixe/extraia o projeto

Extraia o `.zip` em uma pasta, por exemplo `Documentos/wb-edu-agent`.
Abra o terminal **dentro dessa pasta** (isso é importante — os comandos
abaixo só funcionam se você estiver na pasta raiz do projeto, a que
contém o arquivo `run_demo.py`).

```bash
cd caminho/para/wb-edu-agent
```

## Passo 2 (recomendado) — Crie um ambiente virtual

Isso evita 90% dos problemas de instalação (conflito com outros
projetos Python, erro "externally-managed-environment" no Linux, etc.):

```bash
python3 -m venv .venv
```

Ative o ambiente virtual:

- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
- **Windows (CMD):** `.venv\Scripts\activate.bat`
- **Mac/Linux:** `source .venv/bin/activate`

Se der erro de "execução de scripts desabilitada" no PowerShell, rode
antes: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

Você vai ver `(.venv)` aparecer no início da linha do terminal — isso
confirma que está ativado.

## Passo 3 — Rode tudo com um único comando

```bash
python run_demo.py
```

Esse script sozinho:
- instala as dependências (e corrige automaticamente o erro comum
  `externally-managed-environment` do Ubuntu/Debian/WSL);
- tenta buscar dados reais do World Bank pela internet;
- se não conseguir (sem internet, firewall, etc.), **usa o dataset de
  amostra automaticamente** — nunca trava por causa disso;
- roda a limpeza e a análise (rankings, crescimento, agregações);
- se você já tiver configurado a chave da API do Claude (Passo 4
  abaixo), gera também o relatório executivo com IA;
- e, em seguida, gera a versão rica em HTML (cartões de KPI + gráficos)
  e, se o `wkhtmltopdf` estiver instalado
  (https://wkhtmltopdf.org/downloads.html), também em PDF.

Ao final, ele te diz exatamente onde estão os arquivos gerados.

## Passo 4 (opcional, mas recomendado para o vídeo) — Chave da API do Claude

Para a etapa de IA rodar, você precisa de uma chave em
https://console.anthropic.com/settings/keys

```bash
# Mac/Linux
export ANTHROPIC_API_KEY="sua-chave-aqui"

# Windows PowerShell
$env:ANTHROPIC_API_KEY="sua-chave-aqui"
```

Depois rode de novo: `python run_demo.py`

## Se algo ainda der errado

Copie a mensagem de erro **completa** que aparece no terminal (do jeito
que o script imprime — ele já tenta explicar a causa mais provável) e
me envie. Erros comuns e o que costumam significar:

| Mensagem                                   | Causa provável                                          |
|--------------------------------------------|----------------------------------------------------------|
| `command not found: python3`               | Python não instalado ou não está no PATH                |
| `No module named src`                      | Você rodou o comando fora da pasta raiz do projeto        |
| `externally-managed-environment`           | Falta usar ambiente virtual (Passo 2) — o script já trata isso |
| `403 Forbidden` ao consultar o World Bank   | Firewall/proxy da sua rede bloqueando; use o dataset de amostra (automático) |
| `EnvironmentError: ANTHROPIC_API_KEY`      | Falta configurar a chave (Passo 4)                        |

## Para o vídeo

Uma sequência simples de mostrar:
1. Mostrar a estrutura de pastas do projeto (`src/`, `data/`, `reports/`).
2. Rodar `python run_demo.py` ao vivo, mostrando cada etapa no terminal.
3. Abrir `data/processed/final_report_data.csv` e `growth_analysis.csv`.
4. Abrir `reports/executive_report.md` (se a IA rodou) e comentar os
   insights gerados.
5. Mostrar o `n8n/workflow.json` importado no n8n (print ou tela ao vivo)
   como a versão "orquestrada" do mesmo fluxo.
