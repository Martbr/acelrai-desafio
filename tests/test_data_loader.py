"""
Testes unitários para src/data_loader.py.

Rodar com: pytest tests/ -v
"""

import numpy as np
import pandas as pd
import pytest

from src.data_loader import clean_data, handle_missing_values


@pytest.fixture
def raw_sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "country_name": ["Brazil", "Brazil", "Brazil", "World", "  Chile "],
            "country_code": ["BRA", "BRA", "BRA", "WLD", "CHL"],
            "indicator_name": ["Enrollment"] * 5,
            "indicator_code": ["SE.PRM.ENRR"] * 5,
            "year": [2010, 2010, 2011, 2011, 2011],
            "value": [95.0, 95.0, np.nan, 50.0, 88.0],
        }
    )


def test_clean_data_removes_duplicates(raw_sample_df):
    cleaned = clean_data(raw_sample_df)
    brazil_2010 = cleaned[(cleaned["country_code"] == "BRA") & (cleaned["year"] == 2010)]
    assert len(brazil_2010) == 1


def test_clean_data_removes_aggregate_regions(raw_sample_df):
    cleaned = clean_data(raw_sample_df)
    assert "WLD" not in cleaned["country_code"].values


def test_clean_data_strips_whitespace(raw_sample_df):
    cleaned = clean_data(raw_sample_df)
    assert "Chile" in cleaned["country_name"].values
    assert " Chile " not in cleaned["country_name"].values


def test_handle_missing_values_interpolates():
    df = pd.DataFrame(
        {
            "country_name": ["Brazil"] * 4,
            "country_code": ["BRA"] * 4,
            "indicator_code": ["SE.PRM.ENRR"] * 4,
            "year": [2010, 2011, 2012, 2013],
            "value": [100.0, np.nan, np.nan, 106.0],
        }
    )
    filled = handle_missing_values(df)
    assert filled["value"].isna().sum() == 0
    # interpolação linear: 2011 e 2012 devem ficar entre 100 e 106
    values_sorted = filled.sort_values("year")["value"].tolist()
    assert values_sorted == pytest.approx([100.0, 102.0, 104.0, 106.0])


def test_handle_missing_values_drops_fully_empty_series():
    df = pd.DataFrame(
        {
            "country_name": ["Brazil"] * 2,
            "country_code": ["BRA"] * 2,
            "indicator_code": ["SE.PRM.ENRR"] * 2,
            "year": [2010, 2011],
            "value": [np.nan, np.nan],
        }
    )
    filled = handle_missing_values(df)
    assert filled.empty
