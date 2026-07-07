#!/usr/bin/env python3
"""
run_demo.py

PONTO DE ENTRADA ÚNICO do projeto. Feito para rodar o pipeline inteiro
com o mínimo de passos possível — ideal para gravar o vídeo de
apresentação sem depender de configurar venv, n8n, etc.

O que ele faz, em ordem, sempre imprimindo o que está acontecendo:
  1. Confere a versão do Python.
  2. Instala as dependências do requirements.txt (se necessário).
  3. Tenta consultar dados reais do World Bank (internet). Se falhar
     (sem internet, timeout, etc.), avisa e segue com o dataset de
     amostra incluso no repositório — o projeto NUNCA trava por causa
     disso.
  4. Roda a limpeza + análise (rankings, crescimento, agregações).
  5. Se ANTHROPIC_API_KEY estiver configurada, gera o relatório
     executivo com IA. Se não estiver, avisa e pula essa etapa (mas todo
     o resto já fica pronto para mostrar no vídeo).

Uso:
    python3 run_demo.py
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def load_env_file() -> None:
    """Carrega variáveis do .env, se o python-dotenv já estiver disponível."""
    try:
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / ".env")
    except ImportError:
        pass  # python-dotenv ainda não instalado; tentaremos de novo após a instalação


# Melhor esforço já no import do módulo (funciona se dotenv já estava instalado)
load_env_file()


def _print_step(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def check_python_version() -> None:
    _print_step("1/5 - Verificando versão do Python")
    major, minor = sys.version_info[:2]
    print(f"Python detectado: {sys.version.split()[0]}")
    if (major, minor) < (3, 9):
        print(
            "AVISO: recomendamos Python 3.9 ou superior. Se algo der erro nos "
            "próximos passos, esse pode ser o motivo."
        )
    else:
        print("OK - versão compatível.")


CORE_PACKAGES = {"pandas": "pandas", "numpy": "numpy", "requests": "requests", "dotenv": "python-dotenv"}
OPTIONAL_PACKAGES = {"anthropic": "anthropic", "matplotlib": "matplotlib", "markdown": "markdown"}


def _missing_packages(packages: dict[str, str]) -> list[str]:
    """Confere quais dependências (de um conjunto dado) ainda não estão instaladas."""
    missing = []
    for import_name, pip_name in packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pip_name)
    return missing


def _pip_install(packages: list[str], timeout_seconds: int = 240) -> bool:
    """Tenta instalar uma lista de pacotes. Retorna True se deu certo."""
    base_cmd = [sys.executable, "-m", "pip", "install", *packages]

    try:
        result = subprocess.run(base_cmd + ["-q"], capture_output=True, text=True, timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        print(
            f"A instalação de {packages} passou de {timeout_seconds}s sem terminar "
            "(provavelmente compilando alguma biblioteca do zero). Abortando esta tentativa."
        )
        return False

    if result.returncode == 0:
        return True

    combined_output = result.stdout + result.stderr
    if "externally-managed-environment" in combined_output:
        print(
            "Detectado bloqueio 'externally-managed-environment' do seu sistema "
            "(comum em Ubuntu/Debian/WSL). Tentando novamente com --break-system-packages..."
        )
        try:
            result2 = subprocess.run(
                base_cmd + ["-q", "--break-system-packages"],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return False
        if result2.returncode == 0:
            return True
        print(result2.stdout)
        print(result2.stderr)
        return False

    print(result.stdout)
    print(result.stderr)
    return False


def install_dependencies() -> None:
    _print_step("2/5 - Instalando dependências (requirements.txt)")

    if sys.version_info[:2] >= (3, 13):
        print(
            f"AVISO: você está no Python {sys.version.split()[0]}, uma versão bem "
            "recente. Algumas bibliotecas podem não ter pacote pronto (wheel) para "
            "essa versão ainda, o que faz o pip tentar compilar do zero e demorar "
            "muito (ou parecer travado). Se algo travar abaixo, considere usar "
            "Python 3.11 ou 3.12 para este projeto."
        )

    # 1) Dependências essenciais (necessárias para etapas 3 e 4 - dados e análise)
    missing_core = _missing_packages(CORE_PACKAGES)
    if not missing_core:
        print("OK - pandas, numpy e requests já estão instalados.")
    else:
        print(f"Instalando dependências essenciais: {', '.join(missing_core)}...")
        if not _pip_install(missing_core):
            print(
                "\nERRO: não consegui instalar pandas/numpy/requests automaticamente.\n"
                "Sem essas três bibliotecas o pipeline não roda. Tente manualmente:\n"
                f"    {sys.executable} -m pip install {' '.join(missing_core)}\n\n"
                "Se for ambiente virtual, confirme que ele está ativado (deve aparecer "
                "'(.venv)' no início da linha do terminal).\n"
            )
            raise SystemExit(1)
        print("OK - dependências essenciais instaladas.")

    # 2) Dependência opcional (só necessária para a etapa 5 - relatório com IA)
    missing_optional = _missing_packages(OPTIONAL_PACKAGES)
    if not missing_optional:
        print("OK - biblioteca 'anthropic' já está instalada.")
    else:
        print(f"Instalando dependência opcional (IA): {', '.join(missing_optional)}...")
        if _pip_install(missing_optional):
            print("OK - biblioteca 'anthropic' instalada.")
        else:
            print(
                "AVISO: não consegui instalar a biblioteca 'anthropic' automaticamente.\n"
                "Isso NÃO impede o resto do pipeline de rodar (etapas 3 e 4 seguem "
                "normalmente). Só a etapa 5 (relatório com IA) será pulada.\n"
                "Para tentar de novo manualmente depois: "
                f"{sys.executable} -m pip install anthropic\n"
            )


def fetch_real_data() -> None:
    _print_step("3/5 - Consultando dados reais do World Bank (API pública)")
    try:
        subprocess.run(
            [sys.executable, "-m", "src.fetch_worldbank_data"],
            check=True,
            cwd=PROJECT_ROOT,
            timeout=300,
        )
        print("OK - dados reais do World Bank salvos em data/raw/international_education.csv")
    except Exception as exc:  # noqa: BLE001 - queremos capturar qualquer falha de rede
        print(
            f"AVISO: não foi possível consultar a API do World Bank agora ({exc}).\n"
            "Isso pode ser falta de internet, firewall, ou instabilidade da API.\n"
            "Sem problema: o pipeline vai continuar usando o dataset de amostra "
            "incluso no repositório (data/raw/sample_education_data.csv), que tem "
            "o mesmo formato dos dados reais."
        )


def run_pipeline() -> None:
    _print_step("4/5 - Rodando limpeza, análise, rankings e crescimento")
    result = subprocess.run(
        [sys.executable, "-m", "src.pipeline"], cwd=PROJECT_ROOT
    )
    if result.returncode != 0:
        print(
            "ERRO ao rodar o pipeline. Copie a mensagem de erro acima e me envie "
            "para eu te ajudar a corrigir."
        )
        raise SystemExit(1)
    print("OK - CSV final e resumo para IA gerados em data/processed/")


def generate_ai_report() -> None:
    _print_step("5/6 - Gerando relatório executivo com IA (Claude)")
    import os

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "AVISO: variável de ambiente ANTHROPIC_API_KEY não encontrada.\n"
            "Essa etapa foi PULADA. Para gerar o relatório com IA, configure a "
            "chave e rode novamente:\n"
            "  Linux/Mac:   export ANTHROPIC_API_KEY='sua-chave'\n"
            "  Windows PowerShell: $env:ANTHROPIC_API_KEY='sua-chave'\n"
            "Depois rode: python3 -m src.ai_report"
        )
        return False

    result = subprocess.run([sys.executable, "-m", "src.ai_report"], cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print(
            "ERRO ao chamar a API do Claude. Verifique se a chave está correta e "
            "se você tem créditos disponíveis na conta Anthropic."
        )
        return False
    print("OK - relatório executivo salvo em reports/executive_report.md")
    return True


def generate_rich_report(ai_report_ready: bool) -> None:
    _print_step("6/6 - Gerando versão rica em HTML + PDF (KPIs e gráficos)")

    if not ai_report_ready:
        print("AVISO: etapa anterior não rodou, então não há texto de IA para incluir. Pulando esta etapa.")
        return

    import shutil

    if shutil.which("wkhtmltopdf") is None:
        print(
            "AVISO: 'wkhtmltopdf' não encontrado no PATH. O PDF será PULADO, mas o "
            "HTML (com os mesmos gráficos e KPIs) será gerado normalmente.\n"
            "Para também ter o PDF, instale em https://wkhtmltopdf.org/downloads.html "
            "e rode de novo."
        )

    result = subprocess.run([sys.executable, "-m", "src.export_pdf"], cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print("ERRO ao gerar a versão rica em HTML/PDF. Rode manualmente para ver o erro: python3 -m src.export_pdf")
        return
    print("OK - reports/executive_report.html e reports/executive_report.pdf gerados.")


def print_summary() -> None:
    _print_step("RESUMO - onde ver os resultados")
    print(
        "- data/raw/international_education.csv (ou sample_education_data.csv): dados de entrada\n"
        "- data/processed/final_report_data.csv: dados tratados e consolidados\n"
        "- data/processed/growth_analysis.csv: crescimento por país/indicador\n"
        "- data/processed/summary_for_ai.json: resumo estruturado usado pela IA\n"
        "- reports/executive_report.md: relatório executivo em texto (se a etapa 5 rodou)\n"
        "- reports/executive_report.html / .pdf: versão rica com KPIs e gráficos (se a etapa 6 rodou)\n"
    )


def main() -> None:
    check_python_version()
    install_dependencies()
    load_env_file()  # tenta de novo, agora que python-dotenv já deve estar instalado
    fetch_real_data()
    run_pipeline()
    ai_report_ready = generate_ai_report()
    generate_rich_report(ai_report_ready)
    print_summary()
    print("\nPronto! Este é o estado atual do projeto.\n")


if __name__ == "__main__":
    main()
