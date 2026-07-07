"""
Testes unitários para src/analysis.py.

Rodar com: pytest tests/ -v
"""

import pandas as pd
import pytest

from src.analysis import (
    calculate_growth,
    classify_trend,
    compare_countries,
    rank_countries_by_indicator,
)


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "country_name": ["Brazil", "Brazil", "Chile", "Chile", "Peru", "Peru"],
            "country_code": ["BRA", "BRA", "CHL", "CHL", "PER", "PER"],
            "indicator_code": ["SE.TER.ENRR"] * 6,
            "year": [2010, 2020, 2010, 2020, 2010, 2020],
            "value": [30.0, 60.0, 50.0, 55.0, 40.0, 20.0],
        }
    )


def test_calculate_growth_pct_and_cagr(sample_df):
    growth = calculate_growth(sample_df)
    brazil_row = growth[growth["country_code"] == "BRA"].iloc[0]

    assert brazil_row["pct_change"] == pytest.approx(100.0)
    assert brazil_row["cagr_pct"] > 0
    assert brazil_row["first_year"] == 2010
    assert brazil_row["last_year"] == 2020


def test_classify_trend_labels():
    assert classify_trend(50.0) == "evoluiu"
    assert classify_trend(-50.0) == "regrediu"
    assert classify_trend(0.5) == "estagnado"
    assert classify_trend(float("nan")) == "indefinido"


def test_rank_countries_by_indicator_orders_descending(sample_df):
    ranking = rank_countries_by_indicator(sample_df, "SE.TER.ENRR", year=2020, top_n=3)
    assert list(ranking["country_name"]) == ["Brazil", "Chile", "Peru"]
    assert list(ranking["rank"]) == [1, 2, 3]


def test_compare_countries_returns_wide_series(sample_df):
    comparison = compare_countries(sample_df, ["BRA", "CHL"], "SE.TER.ENRR")
    assert set(comparison.columns) == {"Brazil", "Chile"}
    assert comparison.loc[2020, "Brazil"] == 60.0
