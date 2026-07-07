"""
pipeline.py

Ponto de entrada único do pipeline. É este script que o n8n executa
(nó "Execute Command") a cada disparo do workflow.

Fluxo:
  1. Carrega e limpa os dados brutos (data_loader)
  2. Seleciona indicadores/países de interesse (indicators)
  3. Roda as análises: agregações, rankings, crescimento (analysis)
  4. Gera o CSV final consolidado (data/processed/final_report_data.csv)
  5. Gera um resumo em JSON (data/processed/summary_for_ai.json) enxuto
     o suficiente para ser enviado à API do Claude sem estourar contexto,
     mas rico o bastante para permitir análise real (não só números soltos)

Uso:
    python -m src.pipeline
    python -m src.pipeline --countries BRA USA CHN --indicators SE.TER.ENRR
"""

from __future__ import annotations

import argparse
import json
import logging

import pandas as pd

from src.analysis import build_full_analysis
from src.config import FINAL_CSV_PATH, SUMMARY_JSON_PATH, TOP_N_RANKING
from src.data_loader import load_and_prepare_data
from src.indicators import select_countries, select_indicators, to_wide_format

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pipeline de monitoramento educacional")
    parser.add_argument(
        "--countries", nargs="*", default=None, help="Códigos ISO3 dos países (ex: BRA USA CHN)"
    )
    parser.add_argument(
        "--indicators", nargs="*", default=None, help="Códigos de indicadores do World Bank"
    )
    parser.add_argument(
        "--top-n", type=int, default=TOP_N_RANKING, help="Tamanho do ranking por indicador"
    )
    return parser.parse_args()


def build_summary_for_ai(df: pd.DataFrame, analysis_results: dict, top_n: int) -> dict:
    """
    Monta um resumo compacto (não o dataset inteiro) para enviar à IA.
    Inclui apenas o que é necessário para gerar insights: extremos de
    crescimento, rankings por indicador e estatísticas agregadas.
    """
    growth_df = analysis_results["growth"]
    aggregation_df = analysis_results["aggregation"]
    rankings = analysis_results["rankings"]

    top_growth = (
        growth_df.sort_values("pct_change", ascending=False)
        .head(top_n)[["country_name", "indicator_code", "pct_change", "cagr_pct", "trend"]]
        .to_dict(orient="records")
    )
    top_decline = (
        growth_df.sort_values("pct_change", ascending=True)
        .head(top_n)[["country_name", "indicator_code", "pct_change", "cagr_pct", "trend"]]
        .to_dict(orient="records")
    )
    stagnant = (
        growth_df[growth_df["trend"] == "estagnado"]
        .head(top_n)[["country_name", "indicator_code", "pct_change", "trend"]]
        .to_dict(orient="records")
    )

    rankings_serialized = {
        code: rank_df.to_dict(orient="records") for code, rank_df in rankings.items()
    }

    top_investment = (
        aggregation_df[aggregation_df["indicator_code"] == "SE.XPD.TOTL.GD.ZS"]
        .sort_values("mean_value", ascending=False)
        .head(top_n)[["country_name", "mean_value"]]
        .to_dict(orient="records")
    )

    return {
        "period_covered": {
            "min_year": int(df["year"].min()),
            "max_year": int(df["year"].max()),
        },
        "countries_analyzed": sorted(df["country_name"].unique().tolist()),
        "indicators_analyzed": sorted(df["indicator_code"].unique().tolist()),
        "top_growth": top_growth,
        "top_decline": top_decline,
        "stagnant_examples": stagnant,
        "top_investment_pct_gdp": top_investment,
        "rankings_by_indicator": rankings_serialized,
    }


def run_pipeline(
    country_codes: list[str] | None = None,
    indicator_codes: list[str] | None = None,
    top_n: int = TOP_N_RANKING,
) -> dict:
    logger.info("Iniciando pipeline de monitoramento educacional...")

    df = load_and_prepare_data()
    df = select_indicators(df, indicator_codes)
    df = select_countries(df, country_codes)

    if df.empty:
        raise ValueError(
            "Nenhum dado restou após os filtros de país/indicador. Verifique os códigos informados."
        )

    analysis_results = build_full_analysis(df)

    # ---- CSV final consolidado (Atividade Python obrigatória: geração de CSV final) ----
    wide_df = to_wide_format(df)
    growth_df = analysis_results["growth"]

    FINAL_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    wide_df.to_csv(FINAL_CSV_PATH, index=False)
    logger.info("CSV final salvo em %s (%s linhas)", FINAL_CSV_PATH, len(wide_df))

    growth_csv_path = FINAL_CSV_PATH.parent / "growth_analysis.csv"
    growth_df.to_csv(growth_csv_path, index=False)
    logger.info("CSV de crescimento salvo em %s", growth_csv_path)

    # ---- Resumo para a IA ----
    summary = build_summary_for_ai(df, analysis_results, top_n)
    SUMMARY_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SUMMARY_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    logger.info("Resumo para IA salvo em %s", SUMMARY_JSON_PATH)

    logger.info("Pipeline concluído com sucesso.")
    return summary


if __name__ == "__main__":
    args = parse_args()
    result_summary = run_pipeline(args.countries, args.indicators, args.top_n)
    print(json.dumps({"status": "ok", "summary_preview": result_summary["countries_analyzed"]}, ensure_ascii=False))
