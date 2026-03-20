"""
Generate realistic synthetic sample data for ph-labor-analysis.

Used as fallback when PostgreSQL (ph-economic-tracker) is not available.
Data follows real Philippine economic history:
  - GDP: from ~$100B (2005) to ~$437B (2024), with 2009 GFC dip and 2020 COVID shock
  - CPI: base 100 in 2018, monthly series 2005–2024
  - OFW Remittances: $14B (2005) to $37B (2024), annual series
  - Economic dashboard: wide join of all three

Run: python scripts/generate_sample_data.py
Output: data/sample/*.csv
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "sample"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(42)  # reproducible


# ── GDP Trend (annual, 2000–2024) ─────────────────────────────────────────────

def generate_gdp() -> pd.DataFrame:
    years = list(range(2000, 2025))
    # Base GDP at 2000 = ~$81B, growing ~6% CAGR with shocks
    gdp = [81.0]
    growth_rates = {
        2001: 2.9, 2002: 3.6, 2003: 5.0, 2004: 6.4, 2005: 4.8,
        2006: 5.3, 2007: 6.6, 2008: 4.2, 2009: 1.1,  # GFC dip
        2010: 7.6, 2011: 3.7, 2012: 6.7, 2013: 7.1, 2014: 6.0,
        2015: 6.1, 2016: 6.9, 2017: 6.7, 2018: 6.2, 2019: 6.1,
        2020: -9.5,  # COVID shock
        2021: 5.7, 2022: 7.6, 2023: 5.6, 2024: 5.8,
    }
    for yr in years[1:]:
        rate = growth_rates.get(yr, 5.5) / 100
        prev = gdp[-1]
        gdp.append(round(prev * (1 + rate), 2))

    df = pd.DataFrame({
        "period_year": years,
        "period_date": [f"{y}-01-01" for y in years],
        "gdp_usd": [g * 1_000_000_000 for g in gdp],
        "gdp_usd_bn": gdp,
        "gdp_growth_pct": [None] + [growth_rates.get(y, 5.5) for y in years[1:]],
        "gdp_per_capita_usd": [
            round((g * 1_000_000_000) / (pop * 1_000_000), 0)
            for g, pop in zip(
                gdp,
                [80.9, 82.0, 83.1, 84.2, 85.3, 86.3, 87.4, 88.6, 89.7, 90.8,
                 92.0, 93.3, 94.8, 96.7, 98.4, 100.0, 101.6, 103.3, 105.2, 107.0,
                 108.7, 110.2, 111.6, 113.0, 114.3],
            )
        ],
        "prev_gdp_usd": [None] + [g * 1_000_000_000 for g in gdp[:-1]],
        "gdp_yoy_change_usd": [None] + [
            round((gdp[i] - gdp[i-1]) * 1_000_000_000, 0)
            for i in range(1, len(gdp))
        ],
    })
    return df


# ── CPI Trend (monthly, Jan 2000 – Dec 2024) ─────────────────────────────────

def generate_cpi() -> pd.DataFrame:
    dates = pd.date_range("2000-01-01", "2024-12-01", freq="MS")
    # CPI indexed to 2018 base = 100
    # Monthly index constructed so Jan 2018 ≈ 100
    n = len(dates)
    base_idx = list(dates).index(pd.Timestamp("2018-01-01"))

    # Underlying trend: slow drift up
    trend = np.linspace(65, 148, n)

    # Seasonality: rice-price spike in Aug-Sep, low in Jan-Feb
    months = dates.month
    seasonal = 0.8 * np.sin((months - 3) * np.pi / 6)

    # Shocks
    noise = rng.normal(0, 0.3, n)
    shocks = np.zeros(n)
    # 2008 food crisis
    for i, d in enumerate(dates):
        if d.year == 2008 and d.month in [6, 7, 8, 9]:
            shocks[i] = 3.0
        # 2018 rice tariff
        if d.year == 2018 and d.month in [8, 9, 10, 11]:
            shocks[i] = 2.5
        # 2022-2023 post-COVID inflation
        if d.year == 2022:
            shocks[i] = 1.5 + (d.month - 1) * 0.2
        if d.year == 2023 and d.month <= 6:
            shocks[i] = 3.5 - d.month * 0.3

    raw = trend + seasonal + noise + shocks
    # Normalize so 2018 Jan = 100
    scale = 100.0 / raw[base_idx]
    cpi_index = np.round(raw * scale, 2)

    # YoY inflation
    inflation = [None] * 12
    for i in range(12, n):
        yoy = round((cpi_index[i] - cpi_index[i - 12]) / cpi_index[i - 12] * 100, 2)
        inflation.append(yoy)

    # MoM change
    mom_change = [None] + list(np.round(np.diff(cpi_index), 2))
    mom_pct = [None] + [
        round((cpi_index[i] - cpi_index[i-1]) / cpi_index[i-1] * 100, 2)
        for i in range(1, n)
    ]
    prev_cpi = [None] + list(cpi_index[:-1])

    df = pd.DataFrame({
        "period_date": dates.strftime("%Y-%m-%d"),
        "period_year": dates.year,
        "period_month": dates.month,
        "period_quarter": dates.quarter,
        "cpi_index": cpi_index,
        "inflation_pct": inflation,
        "inflation_pct_wb": [None] * n,  # annual WB series not monthly
        "period_label": dates.strftime("%Y-%m"),
        "prev_cpi_index": prev_cpi,
        "cpi_mom_change": mom_change,
        "cpi_mom_pct": mom_pct,
    })
    return df


# ── OFW Remittance Trend (annual, 2000–2024) ─────────────────────────────────

def generate_remittances() -> pd.DataFrame:
    years = list(range(2000, 2025))

    # Real PH remittance history approximation (USD billions)
    remit_bn = [
        6.05, 6.96, 7.38, 7.57, 8.55, 10.69, 12.76, 14.45, 15.93, 17.35,
        18.76, 20.12, 21.39, 22.97, 24.35, 25.61, 26.90, 28.06, 29.20, 30.13,
        29.94,  # 2020 COVID (surprisingly resilient)
        29.86,  # 2021 slightly lower
        31.42,  # 2022 recovery
        36.14,  # 2023 strong
        37.20,  # 2024 est.
    ]

    # GDP bn for pct calculation (from generate_gdp)
    gdp_bn = [81.0]
    growth_rates_for_remit = [
        2.9, 3.6, 5.0, 6.4, 4.8, 5.3, 6.6, 4.2, 1.1,
        7.6, 3.7, 6.7, 7.1, 6.0, 6.1, 6.9, 6.7, 6.2, 6.1,
        -9.5, 5.7, 7.6, 5.6, 5.8,
    ]
    for r in growth_rates_for_remit:
        gdp_bn.append(round(gdp_bn[-1] * (1 + r/100), 2))

    pct_gdp = [round(r / g * 100, 2) for r, g in zip(remit_bn, gdp_bn)]
    usd_values = [round(r * 1_000_000_000, 0) for r in remit_bn]
    prev_usd = [None] + usd_values[:-1]
    yoy_change = [None] + [round(usd_values[i] - usd_values[i-1], 0) for i in range(1, len(usd_values))]
    yoy_pct = [None] + [
        round((usd_values[i] - usd_values[i-1]) / usd_values[i-1] * 100, 2)
        for i in range(1, len(usd_values))
    ]
    # 3-year rolling average (USD bn)
    rolling_3yr = []
    for i in range(len(remit_bn)):
        if i < 2:
            rolling_3yr.append(round(np.mean(remit_bn[:i+1]), 3))
        else:
            rolling_3yr.append(round(np.mean(remit_bn[i-2:i+1]), 3))

    df = pd.DataFrame({
        "period_year": years,
        "period_date": [f"{y}-01-01" for y in years],
        "source": "WORLD_BANK",
        "remittance_usd": usd_values,
        "remittance_usd_bn": remit_bn,
        "remittance_pct_gdp": pct_gdp,
        "ofw_count": [None] * len(years),
        "period_label": [str(y) for y in years],
        "prev_remittance_usd": prev_usd,
        "remittance_yoy_change_usd": yoy_change,
        "remittance_yoy_pct": yoy_pct,
        "remittance_3yr_avg_bn": rolling_3yr,
    })
    return df


# ── Economic Dashboard (wide join, annual) ────────────────────────────────────

def generate_dashboard(gdp_df, cpi_df, remit_df) -> pd.DataFrame:
    # Annual CPI average from monthly
    cpi_annual = (
        cpi_df.groupby("period_year")
        .agg(
            avg_cpi_index=("cpi_index", "mean"),
            avg_inflation_pct=("inflation_pct", "mean"),
        )
        .round(2)
        .reset_index()
    )

    dash = gdp_df[["period_year", "gdp_usd_bn", "gdp_growth_pct", "gdp_per_capita_usd"]].merge(
        cpi_annual, on="period_year", how="outer"
    ).merge(
        remit_df[["period_year", "remittance_usd_bn", "remittance_pct_gdp", "remittance_yoy_pct"]],
        on="period_year", how="outer",
    ).sort_values("period_year").reset_index(drop=True)

    dash["remit_to_gdp_pct_computed"] = (
        dash["remittance_usd_bn"] / dash["gdp_usd_bn"] * 100
    ).round(2)
    return dash


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating synthetic Philippine economic data...")

    gdp = generate_gdp()
    gdp.to_csv(OUTPUT_DIR / "gdp_trend.csv", index=False)
    print(f"  ✓ gdp_trend.csv ({len(gdp)} rows)")

    cpi = generate_cpi()
    cpi.to_csv(OUTPUT_DIR / "cpi_trend.csv", index=False)
    print(f"  ✓ cpi_trend.csv ({len(cpi)} rows)")

    remit = generate_remittances()
    remit.to_csv(OUTPUT_DIR / "remittance_trend.csv", index=False)
    print(f"  ✓ remittance_trend.csv ({len(remit)} rows)")

    dash = generate_dashboard(gdp, cpi, remit)
    dash.to_csv(OUTPUT_DIR / "economic_dashboard.csv", index=False)
    print(f"  ✓ economic_dashboard.csv ({len(dash)} rows)")

    print(f"\nAll sample data written to: {OUTPUT_DIR}")
    print("Run the notebook with this data when PostgreSQL is not available.")
