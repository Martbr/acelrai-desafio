"""
report_builder.py

Monta a versão "rica" do relatório executivo: cartões de KPI, gráficos
reais (matplotlib, embutidos como imagem base64 — o HTML resultante é
autocontido, sem depender de arquivos externos) e o texto da análise da
IA convertido de Markdown para HTML.

Este HTML serve dois propósitos:
  1. Base para gerar o PDF (via export_pdf.py, usando wkhtmltopdf).
  2. Base para o dashboard Streamlit (app.py), que pode embutir o mesmo
     HTML ou reaproveitar as funções de gráfico diretamente.

Mantém a mesma estrutura de seções do prompt da IA (ver
prompts/executive_report_prompt.md) para o relatório ficar coerente do
início ao fim.
"""

from __future__ import annotations

import base64
import io
from datetime import datetime

import markdown as md_lib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

COLOR_GROWTH = "#2E7D32"
COLOR_DECLINE = "#C62828"
COLOR_ACCENT = "#1565C0"
COLOR_GOLD = "#B8860B"

plt.rcParams["font.family"] = "DejaVu Sans"


# --------------------------------------------------------------------------
# Geração de gráficos (matplotlib -> PNG -> base64, para HTML autocontido)
# --------------------------------------------------------------------------
def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def _bar_chart(title: str, labels: list[str], values: list[float], color: str, xlabel: str = "") -> str:
    fig, ax = plt.subplots(figsize=(7, max(2.2, 0.5 * len(labels))))
    y_pos = np.arange(len(labels))
    bars = ax.barh(y_pos, values, color=color, height=0.6, zorder=3)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=11)
    ax.invert_yaxis()
    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.grid(axis="x", linestyle="--", alpha=0.4, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    max_abs = max((abs(v) for v in values), default=1)
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_width() + (max_abs * 0.02),
            bar.get_y() + bar.get_height() / 2,
            f"{value:.1f}",
            va="center",
            fontsize=10,
        )
    fig.tight_layout()
    return _fig_to_base64(fig)


def _scatter_chart(title: str, x: list[float], y: list[float], labels: list[str], xlabel: str, ylabel: str) -> str:
    fig, ax = plt.subplots(figsize=(6.5, 5))
    ax.scatter(x, y, s=90, color=COLOR_ACCENT, alpha=0.8, zorder=3, edgecolor="white", linewidth=1)
    for xi, yi, label in zip(x, y, labels):
        ax.annotate(label, (xi, yi), textcoords="offset points", xytext=(6, 4), fontsize=9)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.grid(linestyle="--", alpha=0.4, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _fig_to_base64(fig)


def _join_rankings(summary: dict, indicator_x: str, indicator_y: str):
    """Junta dois rankings pelo country_code, para montar um gráfico de dispersão."""
    rank_x = {r["country_code"]: r for r in summary["rankings_by_indicator"].get(indicator_x, [])}
    rank_y = {r["country_code"]: r for r in summary["rankings_by_indicator"].get(indicator_y, [])}
    common = sorted(set(rank_x) & set(rank_y))
    labels = [rank_x[c]["country_name"] for c in common]
    xs = [rank_x[c]["value"] for c in common]
    ys = [rank_y[c]["value"] for c in common]
    return labels, xs, ys


# --------------------------------------------------------------------------
# Cartões de KPI
# --------------------------------------------------------------------------
def _kpi_cards_html(summary: dict) -> str:
    period = summary["period_covered"]
    n_countries = len(summary["countries_analyzed"])
    top_grower = summary["top_growth"][0] if summary.get("top_growth") else None
    top_decliner = summary["top_decline"][0] if summary.get("top_decline") else None

    def card(label, value, sub, color):
        return f"""
        <div class="kpi-card">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value" style="color:{color}">{value}</div>
          <div class="kpi-sub">{sub}</div>
        </div>"""

    cards = [
        card("Período analisado", f"{period['min_year']}–{period['max_year']}", f"{n_countries} países", "#333"),
    ]
    if top_grower:
        cards.append(
            card(
                "Maior crescimento",
                f"+{top_grower['pct_change']:.1f}%",
                f"{top_grower['country_name']} ({top_grower['indicator_code']})",
                COLOR_GROWTH,
            )
        )
    if top_decliner:
        cards.append(
            card(
                "Maior queda",
                f"{top_decliner['pct_change']:.1f}%",
                f"{top_decliner['country_name']} ({top_decliner['indicator_code']})",
                COLOR_DECLINE,
            )
        )
    if summary.get("top_investment_pct_gdp"):
        top_inv = summary["top_investment_pct_gdp"][0]
        cards.append(
            card("Maior investimento (% PIB)", f"{top_inv['mean_value']:.1f}%", top_inv["country_name"], COLOR_GOLD)
        )

    return f'<div class="kpi-grid">{"".join(cards)}</div>'


# --------------------------------------------------------------------------
# Montagem do HTML completo
# --------------------------------------------------------------------------
def build_html_report(summary: dict, ai_markdown: str, indicator_names: dict[str, str] | None = None) -> str:
    indicator_names = indicator_names or {}

    kpi_html = _kpi_cards_html(summary)

    growth_chart = None
    if summary.get("top_growth"):
        top = summary["top_growth"][:8]
        growth_chart = _bar_chart(
            "Maior crescimento no período (% de variação)",
            [g["country_name"] for g in top],
            [g["pct_change"] for g in top],
            COLOR_GROWTH,
            "% de variação",
        )

    decline_chart = None
    if summary.get("top_decline"):
        top = summary["top_decline"][:8]
        decline_chart = _bar_chart(
            "Maior queda no período (% de variação)",
            [g["country_name"] for g in top],
            [g["pct_change"] for g in top],
            COLOR_DECLINE,
            "% de variação",
        )

    investment_chart = None
    if summary.get("top_investment_pct_gdp"):
        top = summary["top_investment_pct_gdp"][:8]
        investment_chart = _bar_chart(
            "Maior investimento médio (% do PIB)",
            [i["country_name"] for i in top],
            [i["mean_value"] for i in top],
            COLOR_GOLD,
            "% do PIB (média do período)",
        )

    # Melhores indicadores absolutos: usa o primeiro indicador de matrícula/ensino
    # disponível no ranking (ex: ensino superior) para ilustrar nível absoluto,
    # não crescimento.
    absolute_chart = None
    absolute_indicator = "SE.TER.ENRR" if "SE.TER.ENRR" in summary.get("rankings_by_indicator", {}) else None
    if absolute_indicator:
        top = summary["rankings_by_indicator"][absolute_indicator][:8]
        label = indicator_names.get(absolute_indicator, absolute_indicator)
        absolute_chart = _bar_chart(
            f"Melhores indicadores absolutos — {label}",
            [r["country_name"] for r in top],
            [r["value"] for r in top],
            COLOR_ACCENT,
            "Valor do indicador",
        )

    # Análise incomum: investimento x crescimento (mostra que nem sempre quem
    # investe mais é quem mais cresce)
    scatter_chart = None
    if "SE.XPD.TOTL.GD.ZS" in summary.get("rankings_by_indicator", {}) and "SE.TER.ENRR" in summary.get(
        "rankings_by_indicator", {}
    ):
        labels, xs, ys = _join_rankings(summary, "SE.XPD.TOTL.GD.ZS", "SE.TER.ENRR")
        if labels:
            scatter_chart = _scatter_chart(
                "Investimento (% do PIB) vs. Matrícula no ensino superior",
                xs,
                ys,
                labels,
                "Investimento médio (% do PIB)",
                "Matrícula ensino superior (% bruto)",
            )

    analysis_html = md_lib.markdown(ai_markdown, extensions=["tables"])

    def chart_block(title, img_b64):
        if not img_b64:
            return ""
        return f"""
        <div class="chart-card">
          <img src="data:image/png;base64,{img_b64}" alt="{title}" />
        </div>"""

    charts_html = (
        chart_block("Crescimento", growth_chart)
        + chart_block("Queda", decline_chart)
        + chart_block("Investimento", investment_chart)
        + chart_block("Absoluto", absolute_chart)
    )
    scatter_html = chart_block("Dispersão", scatter_chart)

    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<title>Relatório Executivo - Indicadores Educacionais</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, Helvetica, sans-serif; color: #222; max-width: 960px; margin: 0 auto; padding: 32px; line-height: 1.6; background: #fff; }}
  .header {{ background: linear-gradient(135deg, #1B5E20, #2E7D32); color: white; padding: 28px 32px; border-radius: 12px; margin-bottom: 28px; }}
  .header h1 {{ margin: 0 0 6px 0; font-size: 26px; }}
  .header .subtitle {{ opacity: 0.9; font-size: 14px; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-bottom: 32px; }}
  .kpi-card {{ background: #F8F9FA; border: 1px solid #EEE; border-radius: 10px; padding: 16px; text-align: center; }}
  .kpi-label {{ font-size: 12px; color: #777; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 6px; }}
  .kpi-value {{ font-size: 24px; font-weight: 700; }}
  .kpi-sub {{ font-size: 12px; color: #999; margin-top: 4px; }}
  .charts-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 18px; margin-bottom: 12px; }}
  .chart-card {{ background: #FAFAFA; border: 1px solid #EEE; border-radius: 10px; padding: 14px; text-align: center; }}
  .chart-card img {{ max-width: 100%; height: auto; }}
  h2 {{ font-size: 20px; color: #1B5E20; margin-top: 32px; border-bottom: 2px solid #E8F5E9; padding-bottom: 6px; }}
  h3 {{ font-size: 16px; color: #2E7D32; margin-top: 22px; }}
  .meta {{ color: #666; font-size: 13px; margin-top: 24px; padding-top: 16px; border-top: 1px solid #EEE; }}
  table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
  th, td {{ border: 1px solid #DDD; padding: 6px 10px; text-align: left; font-size: 13px; }}
  th {{ background: #F1F8F2; }}
  ul {{ padding-left: 20px; }}
  li {{ margin-bottom: 6px; }}
</style>
</head>
<body>
  <div class="header">
    <h1>📊 Relatório Executivo — Indicadores Educacionais</h1>
    <div class="subtitle">Agente Inteligente de Monitoramento Educacional · World Bank Education Statistics</div>
  </div>

  {kpi_html}

  <h2>Visão geral em gráficos</h2>
  <div class="charts-grid">
    {charts_html}
  </div>
  {f'<div class="charts-grid">{scatter_html}</div>' if scatter_html else ""}

  {analysis_html}

  <div class="meta">
    Gerado automaticamente via pipeline Python + API do Claude em {generated_at}.
  </div>
</body>
</html>"""
