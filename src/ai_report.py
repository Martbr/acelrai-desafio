"""
ai_report.py

Camada de IA do pipeline: transforma os resultados analíticos (rankings,
crescimento, agregações) em um relatório executivo com insights reais,
usando a API do Claude (Anthropic).

Este módulo é usado de duas formas:
  1. Localmente, via `python -m src.ai_report`, para testes/execução manual.
  2. Pelo n8n: o pipeline.py gera um JSON resumido (summary_for_ai.json)
     que o n8n lê e envia diretamente para a API do Claude via nó
     "HTTP Request" (ver n8n/workflow.json). Este módulo replica essa
     mesma chamada em Python, para quem quiser rodar tudo sem n8n.

IMPORTANTE: a IA aqui não deve apenas descrever números. O prompt é
desenhado para forçar análise: causas prováveis, comparações,
recomendações — não um resumo estatístico disfarçado de "insight".
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from src.config import EXECUTIVE_REPORT_MD_PATH, SUMMARY_JSON_PATH

SYSTEM_PROMPT = """\
Você é um analista sênior de políticas educacionais internacionais, atuando \
para um organismo multilateral. Sua função é interpretar indicadores \
educacionais de diferentes países e produzir inteligência acionável para \
tomadores de decisão — não apenas descrever números.

Regras obrigatórias:
- Nunca apenas repita ou resuma os números recebidos; sempre acrescente \
interpretação, hipóteses causais plausíveis e implicações práticas.
- Identifique explicitamente: países que mais evoluíram, países \
estagnados ou em regressão, países com maior investimento relativo, \
países com melhores indicadores absolutos.
- Para cada padrão identificado, proponha possíveis explicações (ex: \
crises econômicas, reformas educacionais, mudanças demográficas) \
deixando claro quando é hipótese e não fato comprovado pelos dados.
- Termine com recomendações concretas e priorizadas.
- Seja direto, use linguagem executiva, evite jargão técnico desnecessário.
"""


def load_summary(path: Path = SUMMARY_JSON_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_user_prompt(summary: dict) -> str:
    return f"""\
Abaixo está um resumo estruturado (JSON) com indicadores educacionais de \
múltiplos países, já processados (rankings, crescimento, agregações).

Gere um RELATÓRIO EXECUTIVO em Markdown com as seções:

1. **Panorama geral** (2-3 parágrafos)
2. **Países em destaque** (maior evolução, com hipóteses do porquê)
3. **Países estagnados ou em regressão** (com hipóteses do porquê)
4. **Investimento vs. resultado** (quem investe mais e o retorno aparente)
5. **Melhores indicadores absolutos** (não confundir com crescimento: quais países têm hoje os melhores números em termos absolutos em cada indicador, usando os rankings fornecidos)
6. **Comparações relevantes entre países**
7. **Recomendações** (priorizadas, acionáveis)

Dados:
```json
{json.dumps(summary, ensure_ascii=False, indent=2)}
```
"""


def generate_executive_report(summary: dict | None = None, model: str = "claude-sonnet-4-6") -> str:
    """
    Chama a API do Claude para gerar o relatório executivo.
    Requer a variável de ambiente ANTHROPIC_API_KEY configurada
    (ex: em um arquivo .env, carregado via python-dotenv).
    """
    try:
        import anthropic
    except ImportError as exc:
        raise ImportError(
            "Instale a biblioteca 'anthropic' (pip install anthropic) para usar este módulo."
        ) from exc

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "Defina a variável de ambiente ANTHROPIC_API_KEY antes de rodar este módulo."
        )

    summary = summary or load_summary()
    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model=model,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_prompt(summary)}],
    )

    report_text = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )
    return report_text


def save_report(report_text: str, path: Path = EXECUTIVE_REPORT_MD_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report_text)


if __name__ == "__main__":
    summary_data = load_summary()
    report = generate_executive_report(summary_data)
    save_report(report)
    print(f"Relatório executivo salvo em {EXECUTIVE_REPORT_MD_PATH}")
