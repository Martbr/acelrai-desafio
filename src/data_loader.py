"""
data_loader.py

Responsável por:
  1. Carregar os dados brutos do World Bank (CSV baixado do Kaggle).
  2. Limpar os dados (tipos, duplicatas, nomes padronizados).
  3. Tratar valores ausentes de forma explícita e documentada.

Estas são duas das quatro atividades Python obrigatórias do projeto:
  - limpeza de dados
  - tratamento de valores ausentes
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.config import (
    MAX_YEAR,
    MIN_YEAR,
    RAW_DATA_FILE_REAL,
    RAW_DATA_FILE_SAMPLE,
    REQUIRED_COLUMNS,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def resolve_raw_data_path() -> Path:
    """
    Decide qual arquivo bruto usar: o dataset real do Kaggle (se já foi
    baixado) ou o dataset de amostra sintética (para demonstração).
    """
    if RAW_DATA_FILE_REAL.exists():
        logger.info("Usando dataset real: %s", RAW_DATA_FILE_REAL)
        return RAW_DATA_FILE_REAL

    if RAW_DATA_FILE_SAMPLE.exists():
        logger.warning(
            "Dataset real não encontrado. Usando dataset de amostra em %s. "
            "Veja data/raw/README.md para baixar o dataset completo do Kaggle.",
            RAW_DATA_FILE_SAMPLE,
        )
        return RAW_DATA_FILE_SAMPLE

    raise FileNotFoundError(
        "Nenhum arquivo de dados encontrado em data/raw/. "
        "Baixe o dataset do Kaggle ou mantenha o sample_education_data.csv."
    )


def load_raw_data(path: Path | None = None) -> pd.DataFrame:
    """Carrega o CSV bruto e valida o schema esperado."""
    path = path or resolve_raw_data_path()
    df = pd.read_csv(path)

    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"Colunas obrigatórias ausentes no dataset: {missing_cols}. "
            f"Esperado: {REQUIRED_COLUMNS}"
        )

    logger.info("Dados brutos carregados: %s linhas, %s colunas", *df.shape)
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpeza de dados (Atividade Python obrigatória #1):
      - remove duplicatas exatas
      - normaliza tipos de coluna (year -> int, value -> float)
      - remove espaços em branco de colunas de texto
      - filtra o intervalo de anos de interesse
      - remove linhas totalmente inválidas (sem country_code ou indicator_code)
    """
    df = df.copy()

    text_cols = ["country_name", "country_code", "indicator_name", "indicator_code"]
    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()

    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    before = len(df)
    df = df.drop_duplicates(
        subset=["country_code", "indicator_code", "year"], keep="first"
    )
    logger.info("Duplicatas removidas: %s", before - len(df))

    df = df.dropna(subset=["country_code", "indicator_code", "year"])

    df = df[(df["year"] >= MIN_YEAR) & (df["year"] <= MAX_YEAR)]

    # Aggregate-level "countries" do World Bank (ex: "World", "Low income")
    # não interessam para comparação entre países individuais.
    aggregate_like = df["country_name"].str.contains(
        r"World|income|region|OECD|Euro area|IDA|IBRD|Arab World",
        case=False,
        regex=True,
        na=False,
    )
    removed = aggregate_like.sum()
    if removed:
        logger.info("Removidos %s registros de agregados regionais/globais", removed)
    df = df[~aggregate_like]

    df = df.reset_index(drop=True)
    logger.info("Dados após limpeza: %s linhas", len(df))
    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tratamento de valores ausentes (Atividade Python obrigatória #2).

    Estratégia:
      - Para cada par (país, indicador), interpola linearmente os anos
        faltantes quando há pontos suficientes nos dois extremos (evita
        "inventar" tendência para séries muito curtas).
      - Preenche bordas remanescentes com forward-fill / backward-fill
        dentro da mesma série (mantendo o último valor conhecido).
      - Remove ao final qualquer combinação (país, indicador) que continue
        100% vazia, pois não há como analisá-la de forma confiável.
    """
    df = df.copy()
    missing_before = df["value"].isna().sum()

    df = df.sort_values(["country_code", "indicator_code", "year"]).reset_index(drop=True)
    df["value"] = df.groupby(["country_code", "indicator_code"])["value"].transform(
        lambda s: s.interpolate(method="linear", limit_direction="both")
    )

    still_missing = df["value"].isna()
    if still_missing.any():
        logger.info(
            "Removendo %s linhas sem nenhum valor observável na série (país+indicador)",
            still_missing.sum(),
        )
        df = df[~still_missing]

    missing_after = df["value"].isna().sum()
    logger.info(
        "Valores ausentes: %s -> %s (tratados via interpolação linear por série)",
        missing_before,
        missing_after,
    )
    return df.reset_index(drop=True)


def load_and_prepare_data() -> pd.DataFrame:
    """Função de conveniência: carrega, limpa e trata valores ausentes."""
    raw_df = load_raw_data()
    clean_df = clean_data(raw_df)
    final_df = handle_missing_values(clean_df)
    return final_df


if __name__ == "__main__":
    data = load_and_prepare_data()
    print(data.head(20))
    print(f"\nTotal de linhas após limpeza e tratamento: {len(data)}")
