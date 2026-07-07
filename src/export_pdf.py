"""
export_pdf.py

Converte o relatório HTML (gerado por report_builder.build_html_report)
em um arquivo PDF, usando o wkhtmltopdf (ferramenta de linha de comando).

Uso:
    python -m src.export_pdf
    (gera reports/executive_report.pdf a partir do summary + relatório
    de IA mais recentes)
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from src.config import EXECUTIVE_REPORT_MD_PATH, INDICATORS_OF_INTEREST, REPORTS_DIR, SUMMARY_JSON_PATH
from src.report_builder import build_html_report


def html_to_pdf(html_content: str, output_path: Path) -> None:
    if shutil.which("wkhtmltopdf") is None:
        raise EnvironmentError(
            "wkhtmltopdf não encontrado no sistema. Instale-o "
            "(https://wkhtmltopdf.org/downloads.html) para gerar PDFs, ou use a "
            "opção de 'Salvar como PDF' do navegador a partir do arquivo .html."
        )

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tmp:
        tmp.write(html_content)
        tmp_path = tmp.name

    try:
        subprocess.run(
            [
                "wkhtmltopdf",
                "--enable-local-file-access",
                "--quiet",
                tmp_path,
                str(output_path),
            ],
            check=True,
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def main() -> None:
    import json

    with open(SUMMARY_JSON_PATH, "r", encoding="utf-8") as f:
        summary = json.load(f)
    with open(EXECUTIVE_REPORT_MD_PATH, "r", encoding="utf-8") as f:
        ai_markdown = f.read()

    html = build_html_report(summary, ai_markdown, INDICATORS_OF_INTEREST)

    # O HTML é sempre gerado - não depende do wkhtmltopdf, e já é utilizável
    # sozinho (abre em qualquer navegador, pode ser enviado por e-mail, etc).
    html_path = REPORTS_DIR / "executive_report.html"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML salvo em {html_path}")

    # O PDF é best-effort: só roda se o wkhtmltopdf estiver disponível.
    # Se não estiver, avisa claramente mas NÃO desfaz o HTML já salvo acima.
    pdf_path = REPORTS_DIR / "executive_report.pdf"
    try:
        html_to_pdf(html, pdf_path)
        print(f"PDF salvo em {pdf_path}")
    except EnvironmentError as exc:
        print(f"AVISO: PDF não gerado ({exc})")
        print(f"O relatório em HTML continua disponível normalmente em {html_path}.")


if __name__ == "__main__":
    main()
