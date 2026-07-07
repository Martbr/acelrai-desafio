"""
Configurações centrais do projeto: caminhos de arquivos, indicadores
monitorados e parâmetros gerais do pipeline.

Manter todas as constantes aqui facilita ajustar o projeto (ex: trocar o
dataset, adicionar indicadores, mudar países de interesse) sem precisar
mexer na lógica dos outros módulos.
"""

from pathlib import Path

try:
    from dotenv import load_dotenv

    # Carrega variáveis de um arquivo .env na raiz do projeto (se existir),
    # ex: ANTHROPIC_API_KEY=sk-ant-xxxx
    # Isso permite configurar a chave uma única vez em um arquivo, em vez de
    # precisar exportar a variável de ambiente toda vez que abrir o terminal.
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    # python-dotenv é opcional: se não estiver instalado, o projeto ainda
    # funciona normalmente usando variáveis de ambiente do sistema.
    pass

# --------------------------------------------------------------------------
# Caminhos
# --------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORTS_DIR = BASE_DIR / "reports"

# Arquivo bruto (baixado do Kaggle). Ver data/raw/README.md para instruções
# de download. Enquanto o dataset real não é baixado, usamos o arquivo de
# amostra sintética para permitir rodar o pipeline de ponta a ponta.
RAW_DATA_FILE_REAL = DATA_RAW_DIR / "international_education.csv"
RAW_DATA_FILE_SAMPLE = DATA_RAW_DIR / "sample_education_data.csv"

FINAL_CSV_PATH = DATA_PROCESSED_DIR / "final_report_data.csv"
SUMMARY_JSON_PATH = DATA_PROCESSED_DIR / "summary_for_ai.json"
EXECUTIVE_REPORT_MD_PATH = REPORTS_DIR / "executive_report.md"

# --------------------------------------------------------------------------
# Indicadores monitorados (códigos oficiais do World Bank)
# --------------------------------------------------------------------------
INDICATORS_OF_INTEREST = {
    "SE.XPD.TOTL.GD.ZS": "Gasto público em educação (% do PIB)",
    "SE.XPD.TOTL.GB.ZS": "Gasto público em educação (% do gasto público total)",
    "SE.PRM.ENRR": "Matrícula no ensino primário (% bruto)",
    "SE.SEC.ENRR": "Matrícula no ensino secundário (% bruto)",
    "SE.TER.ENRR": "Matrícula no ensino superior (% bruto)",
    "SE.ADT.LITR.ZS": "Taxa de alfabetização de adultos (%)",
}

# --------------------------------------------------------------------------
# Parâmetros de análise
# --------------------------------------------------------------------------
MIN_YEAR = 2010
MAX_YEAR = 2022
TOP_N_RANKING = 10

# Colunas obrigatórias esperadas no dataset bruto (schema do World Bank /
# BigQuery public dataset "world_bank_intl_education.international_education")
REQUIRED_COLUMNS = [
    "country_name",
    "country_code",
    "indicator_name",
    "indicator_code",
    "year",
    "value",
]
