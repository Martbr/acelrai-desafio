"""
analysis.py

Responsável pelas atividades analíticas do pipeline:
  - Agregações (médias por país/indicador/período)
  - Rankings (top N países por indicador)
  - Cálculo de crescimento (variação % e CAGR entre o primeiro e o
    último ano disponível de cada série)
  - Comparação entre países

Cobre, sozinho, mais de uma das quatro atividades Python obrigatórias
(agregações, rankings, cálculo de crescimento, comparação entre países).
"""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

from src.config import TOP_N_RANKING


def aggregate_by_country_indicator(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agregação: média, mínimo, máximo e desvio padrão de cada indicador
    por país, considerando todo o período disponível.
    """
    agg = (
        df.groupby(["country_name", "country_code", "indicator_code"])["value"]
        .agg(mean_value="mean", min_value="min", max_value="max", std_value="std")
        .reset_index()
    )
    return agg


def rank_countries_by_indicator(
    df: pd.DataFrame, indicator_code: str, year: int | None = None, top_n: int = TOP_N_RANKING
) -> pd.DataFrame:
    """
    Gera um ranking dos países para um indicador específico.
    Se `year` for informado, usa o valor daquele ano; caso contrário,
    usa o ano mais recente disponível para cada país.
    """
    subset = df[df["indicator_code"] == indicator_code].copy()

    if year is not None:
        subset = subset[subset["year"] == year]
    else:
        idx = subset.groupby("country_code")["year"].idxmax()
        subset = subset.loc[idx]

    ranking = subset.sort_values("value", ascending=False).reset_index(drop=True)
    ranking.insert(0, "rank", ranking.index + 1)
    return ranking.head(top_n)[["rank", "country_name", "country_code", "year", "value"]]


def calculate_growth(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula, para cada par (país, indicador), o crescimento entre o
    primeiro e o último ano disponível na série:
      - variação absoluta
      - variação percentual total
      - CAGR (taxa de crescimento anual composta), quando aplicável
    """
    records = []
    grouped = df.groupby(["country_name", "country_code", "indicator_code"])

    for (country_name, country_code, indicator_code), group in grouped:
        group = group.sort_values("year")
        if len(group) < 2:
            continue

        first_row = group.iloc[0]
        last_row = group.iloc[-1]

        first_value = first_row["value"]
        last_value = last_row["value"]
        n_years = int(last_row["year"] - first_row["year"])

        abs_change = last_value - first_value
        pct_change = (abs_change / first_value * 100) if first_value not in (0, np.nan) else np.nan

        cagr = np.nan
        if n_years > 0 and first_value > 0 and last_value > 0:
            cagr = ((last_value / first_value) ** (1 / n_years) - 1) * 100

        records.append(
            {
                "country_name": country_name,
                "country_code": country_code,
                "indicator_code": indicator_code,
                "first_year": int(first_row["year"]),
                "last_year": int(last_row["year"]),
                "first_value": round(first_value, 2),
                "last_value": round(last_value, 2),
                "abs_change": round(abs_change, 2),
                "pct_change": round(pct_change, 2) if pd.notna(pct_change) else np.nan,
                "cagr_pct": round(cagr, 2) if pd.notna(cagr) else np.nan,
            }
        )

    return pd.DataFrame(records)


def classify_trend(pct_change: float, stagnation_threshold: float = 3.0) -> str:
    """
    Classifica a tendência de um país/indicador com base na variação
    percentual total no período:
      - "evoluiu": crescimento acima do limite de estagnação
      - "estagnado": variação dentro da faixa neutra
      - "regrediu": queda além do limite de estagnação
    """
    if pd.isna(pct_change):
        return "indefinido"
    if pct_change > stagnation_threshold:
        return "evoluiu"
    if pct_change < -stagnation_threshold:
        return "regrediu"
    return "estagnado"


def compare_countries(
    df: pd.DataFrame, country_codes: Iterable[str], indicator_code: str
) -> pd.DataFrame:
    """
    Compara diretamente um conjunto de países para um indicador,
    retornando a série temporal completa lado a lado (formato largo,
    um país por coluna).
    """
    codes = [c.upper() for c in country_codes]
    subset = df[
        (df["indicator_code"] == indicator_code) & (df["country_code"].str.upper().isin(codes))
    ]
    comparison = subset.pivot_table(index="year", columns="country_name", values="value")
    return comparison.sort_index()


def build_full_analysis(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Executa o conjunto completo de análises e retorna um dicionário com
    todos os dataframes resultantes, prontos para exportação/uso pela IA.
    """
    growth_df = calculate_growth(df)
    growth_df["trend"] = growth_df["pct_change"].apply(classify_trend)

    aggregation_df = aggregate_by_country_indicator(df)

    rankings = {}
    for indicator_code in df["indicator_code"].unique():
        rankings[indicator_code] = rank_countries_by_indicator(df, indicator_code)

    return {
        "growth": growth_df,
        "aggregation": aggregation_df,
        "rankings": rankings,
    }


if __name__ == "__main__":
    from src.data_loader import load_and_prepare_data
    from src.indicators import select_indicators

    data = select_indicators(load_and_prepare_data())
    results = build_full_analysis(data)
    print("=== Crescimento (amostra) ===")
    print(results["growth"].head(10))
