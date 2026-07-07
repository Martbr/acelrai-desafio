"""
indicators.py

Responsável por:
  - Seleção de indicadores de interesse (Atividade Python obrigatória #3).
  - Seleção/filtro de países.
  - Transformação para formato "wide" (uma coluna por indicador), que
    facilita comparações e geração de rankings.
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from src.config import INDICATORS_OF_INTEREST


def select_indicators(
    df: pd.DataFrame, indicator_codes: Iterable[str] | None = None
) -> pd.DataFrame:
    """
    Filtra o dataframe para manter apenas os indicadores de interesse.
    Se `indicator_codes` não for informado, usa os indicadores configurados
    em src/config.py (INDICATORS_OF_INTEREST).
    """
    codes = list(indicator_codes) if indicator_codes else list(INDICATORS_OF_INTEREST.keys())
    filtered = df[df["indicator_code"].isin(codes)].copy()
    return filtered


def select_countries(df: pd.DataFrame, country_codes: Iterable[str] | None = None) -> pd.DataFrame:
    """
    Filtra o dataframe para manter apenas os países informados.
    Se `country_codes` for None, retorna todos os países disponíveis.
    """
    if not country_codes:
        return df.copy()
    codes = {c.upper() for c in country_codes}
    return df[df["country_code"].str.upper().isin(codes)].copy()


def to_wide_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converte o dataframe (formato longo: uma linha por país/indicador/ano)
    para formato largo: uma linha por país/ano, uma coluna por indicador.
    Facilita comparação direta entre indicadores de um mesmo país/ano.
    """
    wide = df.pivot_table(
        index=["country_name", "country_code", "year"],
        columns="indicator_code",
        values="value",
        aggfunc="mean",
    ).reset_index()
    wide.columns.name = None
    return wide


def latest_year_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    """
    Retorna, para cada país e indicador, apenas o registro do ano mais
    recente disponível — útil para rankings de "situação atual".
    """
    idx = df.groupby(["country_code", "indicator_code"])["year"].idxmax()
    return df.loc[idx].reset_index(drop=True)


if __name__ == "__main__":
    from src.data_loader import load_and_prepare_data

    data = load_and_prepare_data()
    selected = select_indicators(data)
    wide = to_wide_format(selected)
    print(wide.head(10))
