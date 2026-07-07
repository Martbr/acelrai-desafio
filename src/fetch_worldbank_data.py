"""
fetch_worldbank_data.py

Este módulo é o que efetivamente "consulta os dados do World Bank" de
forma automatizada, sem depender de um dataset sintético.

Contexto: o dataset disponibilizado no Kaggle
(theworldbank/world-bank-intl-education) é um espelho estático da mesma
fonte oficial: a API pública de Indicadores do World Bank
(https://api.worldbank.org). Este script consulta essa API diretamente
e gera um CSV local no MESMO schema do dataset do Kaggle/BigQuery
(country_name, country_code, indicator_name, indicator_code, year, value),
para uso imediato pelo restante do pipeline (data_loader.py em diante).

Por que consultar a API em vez de só baixar o CSV do Kaggle?
  - Não exige conta/token do Kaggle (mais fácil de automatizar em CI/n8n).
  - Sempre traz o dado mais recente disponível (o CSV do Kaggle é uma
    cópia estática, que pode ficar desatualizada).
  - É a mesma fonte primária de dados do World Bank.

Se você preferir usar literalmente o arquivo baixado do Kaggle, isso
também é suportado: basta colocar o CSV baixado em
`data/raw/international_education.csv` (ver data/raw/README.md) — o
data_loader.py usa esse arquivo automaticamente se ele existir, e só cai
para este fetch/API ou para o dataset de amostra se ele não existir.

Uso:
    python -m src.fetch_worldbank_data
    python -m src.fetch_worldbank_data --countries BRA USA CHN --indicators SE.PRM.ENRR SE.TER.ENRR

Requer conexão com a internet (sem autenticação necessária).
"""

from __future__ import annotations

import argparse
import logging
import time
from typing import Iterable

import pandas as pd
import requests

from src.config import DATA_RAW_DIR, INDICATORS_OF_INTEREST, MAX_YEAR, MIN_YEAR

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_URL = "https://api.worldbank.org/v2/country/{countries}/indicator/{indicator}"

DEFAULT_COUNTRIES = [
    "BRA",  # Brazil
    "USA",  # United States
    "DEU",  # Germany
    "JPN",  # Japan
    "IND",  # India
    "CHN",  # China
    "ZAF",  # South Africa
    "ARG",  # Argentina
    "PRT",  # Portugal
    "NGA",  # Nigeria
]


def fetch_indicator(
    countries: Iterable[str],
    indicator_code: str,
    date_range: str,
    per_page: int = 1000,
    timeout: int = 60,
    max_retries: int = 3,
) -> list[dict]:
    """
    Consulta a API do World Bank para um indicador, todos os países e
    anos informados, paginando automaticamente se necessário.

    Faz até `max_retries` tentativas por página em caso de timeout/erro de
    conexão (comum em redes mais lentas ou instáveis), com espera
    progressiva entre tentativas.
    """
    url = BASE_URL.format(countries=";".join(countries), indicator=indicator_code)
    params = {"format": "json", "date": date_range, "per_page": per_page}

    all_records: list[dict] = []
    page = 1
    while True:
        params["page"] = page

        response = None
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, params=params, timeout=timeout)
                response.raise_for_status()
                break
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
                last_error = exc
                wait = attempt * 3
                logger.warning(
                    "  Tentativa %s/%s falhou (%s). Tentando de novo em %ss...",
                    attempt,
                    max_retries,
                    exc.__class__.__name__,
                    wait,
                )
                time.sleep(wait)

        if response is None:
            raise last_error

        payload = response.json()

        if not payload or len(payload) < 2 or payload[1] is None:
            logger.warning("Sem dados retornados para indicador %s", indicator_code)
            break

        meta, records = payload[0], payload[1]
        all_records.extend(records)

        if page >= meta.get("pages", 1):
            break
        page += 1
        time.sleep(0.2)  # boa prática: não sobrecarregar a API pública

    return all_records


def records_to_rows(records: list[dict]) -> list[dict]:
    """Converte os registros da API (JSON) para o schema usado pelo pipeline."""
    rows = []
    for r in records:
        if r.get("value") is None:
            continue
        rows.append(
            {
                "country_name": r["country"]["value"],
                "country_code": r.get("countryiso3code") or r["country"]["id"],
                "indicator_name": r["indicator"]["value"],
                "indicator_code": r["indicator"]["id"],
                "year": int(r["date"]),
                "value": float(r["value"]),
            }
        )
    return rows


def fetch_all(
    countries: list[str] | None = None,
    indicator_codes: list[str] | None = None,
    min_year: int = MIN_YEAR,
    max_year: int = MAX_YEAR,
) -> pd.DataFrame:
    """
    Consulta todos os indicadores de interesse para os países informados.

    Se algum indicador falhar (ex: timeout pontual), o erro é registrado e
    a consulta segue para os próximos indicadores, em vez de descartar tudo
    o que já foi obtido com sucesso.
    """
    countries = countries or DEFAULT_COUNTRIES
    indicator_codes = indicator_codes or list(INDICATORS_OF_INTEREST.keys())
    date_range = f"{min_year}:{max_year}"

    all_rows: list[dict] = []
    failed_indicators: list[str] = []

    for indicator_code in indicator_codes:
        logger.info("Consultando World Bank API: %s (%s países, %s)", indicator_code, len(countries), date_range)
        try:
            records = fetch_indicator(countries, indicator_code, date_range)
            rows = records_to_rows(records)
            logger.info("  -> %s registros com valor válido", len(rows))
            all_rows.extend(rows)
        except Exception as exc:  # noqa: BLE001 - queremos seguir mesmo com falha pontual
            logger.error("  -> Falhou para %s (%s). Seguindo para o próximo indicador.", indicator_code, exc)
            failed_indicators.append(indicator_code)

    if not all_rows:
        raise RuntimeError(
            "Nenhum dado retornado pela API do World Bank (todos os indicadores "
            "falharam). Verifique conexão com a internet, os códigos de "
            "país/indicador informados, e o intervalo de anos."
        )

    if failed_indicators:
        logger.warning(
            "Concluído com falhas parciais. Indicadores não obtidos: %s. "
            "O CSV será salvo apenas com os indicadores que funcionaram.",
            ", ".join(failed_indicators),
        )

    return pd.DataFrame(all_rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Consulta dados reais do World Bank via API pública (sem necessidade de autenticação)."
    )
    parser.add_argument("--countries", nargs="*", default=None, help="Códigos ISO3 (ex: BRA USA CHN)")
    parser.add_argument("--indicators", nargs="*", default=None, help="Códigos de indicador do World Bank")
    parser.add_argument("--min-year", type=int, default=MIN_YEAR)
    parser.add_argument("--max-year", type=int, default=MAX_YEAR)
    args = parser.parse_args()

    df = fetch_all(args.countries, args.indicators, args.min_year, args.max_year)

    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DATA_RAW_DIR / "international_education.csv"
    df.to_csv(output_path, index=False)
    logger.info("Dados reais do World Bank salvos em %s (%s linhas)", output_path, len(df))


if __name__ == "__main__":
    main()
