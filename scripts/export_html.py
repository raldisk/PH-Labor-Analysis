"""
Export ph_economic_eda.ipynb to a self-contained HTML report.

Also generates:
  - output/summary_dashboard.html  (standalone interactive data card)
  - docs/preview.png               (static README chart image)

Usage:
    python scripts/export_html.py

Requires:
    - Notebook must be executed first (all outputs present)
    - pip install nbconvert matplotlib pandas

Output:
    output/ph_economic_eda.html
    output/summary_dashboard.html
    docs/preview.png
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT      = Path(__file__).parent.parent
NB_PATH   = ROOT / "notebooks" / "ph_economic_eda.ipynb"
HTML_PATH = ROOT / "output" / "ph_economic_eda.html"
HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
(ROOT / "docs").mkdir(parents=True, exist_ok=True)


def run_notebook() -> None:
    """
    Execute the notebook and write outputs back to the same path.

    Uses --output instead of --inplace so that nbconvert only overwrites
    the file on success. With --inplace, a mid-execution failure (kernel
    crash, timeout, OOM) leaves the .ipynb in a partially-executed state
    with mixed outputs — hard to debug and inconsistent on the next run.
    """
    print("Executing notebook (this may take 1–2 minutes)...")
    result = subprocess.run(
        [
            sys.executable, "-m", "jupyter", "nbconvert",
            "--to", "notebook",
            "--execute",
            "--output", str(NB_PATH),
            "--ExecutePreprocessor.timeout=300",
            "--ExecutePreprocessor.kernel_name=python3",
            str(NB_PATH),
        ],
        capture_output=False,
    )
    if result.returncode != 0:
        print("Notebook execution failed — check cell errors above.")
        sys.exit(1)
    print("Notebook executed successfully.")


def export_html() -> None:
    """Convert executed notebook to standalone HTML."""
    print("Exporting to HTML...")
    result = subprocess.run(
        [
            sys.executable, "-m", "jupyter", "nbconvert",
            "--to", "html",
            "--no-input",            # hide code cells in the report
            "--output", str(HTML_PATH),
            str(NB_PATH),
        ],
        capture_output=False,
    )
    if result.returncode != 0:
        print("HTML export failed.")
        sys.exit(1)
    size_kb = HTML_PATH.stat().st_size // 1024
    print(f"HTML report written: {HTML_PATH}  ({size_kb:,} KB)")


def export_html_with_code() -> None:
    """Export with code cells visible — for technical reviewers."""
    code_path = HTML_PATH.parent / "ph_economic_eda_with_code.html"
    subprocess.run(
        [
            sys.executable, "-m", "jupyter", "nbconvert",
            "--to", "html",
            "--output", str(code_path),
            str(NB_PATH),
        ],
        capture_output=False,
    )
    size_kb = code_path.stat().st_size // 1024
    print(f"HTML with code:      {code_path}  ({size_kb:,} KB)")


def export_summary_dashboard() -> None:
    """
    Generate output/summary_dashboard.html — a lightweight standalone
    one-page data card with interactive Chart.js charts.

    Self-contained: no server required, no Jupyter, no Python runtime.
    Share with any stakeholder who just wants the headline numbers.
    All data is embedded inline from data/sample/economic_dashboard.csv
    so the file works offline.
    """
    dash_src  = ROOT / "output" / "summary_dashboard.html"
    if not dash_src.exists():
        print("summary_dashboard.html not found in output/ — skipping.")
        return
    size_kb = dash_src.stat().st_size // 1024
    print(f"Summary dashboard:   {dash_src}  ({size_kb:,} KB)")


def export_preview_png() -> None:
    """
    Regenerate docs/preview.png from data/sample/economic_dashboard.csv.

    Produces two side-by-side charts:
      1. GDP (bars) vs Remittances (line), dual-axis.
      2. Remittances % of GDP, highlighting years >= 14%.

    The PNG is referenced in README.md and renders on GitHub.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import pandas as pd

    df = pd.read_csv(ROOT / "data" / "sample" / "economic_dashboard.csv")

    BG     = "#0d1117"
    PANEL  = "#161b22"
    BORDER = "#21262d"
    TEXT   = "#c9d1d9"
    SUBTEXT= "#8b949e"
    BLUE   = "#4c8ed4"
    ORANGE = "#d85a30"
    GREEN  = "#3da679"
    RED    = "#e24b4a"

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), facecolor=BG)
    fig.patch.set_facecolor(BG)

    # ── Chart 1: GDP bars + remittances line ──────────────────────────────
    ax1 = axes[0]
    ax1.set_facecolor(PANEL)
    ax2 = ax1.twinx()

    years = df["period_year"]
    ax1.bar(years, df["gdp_usd_bn"], color=BLUE, alpha=0.55, width=0.7, zorder=2)
    ax2.plot(years, df["remittance_usd_bn"], color=ORANGE, linewidth=2, zorder=3,
             marker="o", markersize=3.5, markerfacecolor=ORANGE)
    ax2.fill_between(years, df["remittance_usd_bn"], alpha=0.08, color=ORANGE)

    for yr, label in [(2009, "GFC"), (2020, "COVID-19")]:
        ax1.axvline(yr, color=RED, linewidth=0.9, linestyle="--", alpha=0.6, zorder=1)
        ax1.text(yr + 0.2, df["gdp_usd_bn"].max() * 0.93, label,
                 color=RED, fontsize=8, alpha=0.8, va="top")

    ax1.set_xlabel("Year", color=SUBTEXT, fontsize=9)
    ax1.set_ylabel("GDP (USD bn)", color=BLUE, fontsize=9)
    ax2.set_ylabel("Remittances (USD bn)", color=ORANGE, fontsize=9)
    ax1.set_title("GDP vs OFW Remittances  2000–2024",
                  color=TEXT, fontsize=10, fontweight="bold", pad=10)

    for ax in [ax1, ax2]:
        ax.tick_params(colors=SUBTEXT, labelsize=8)
        ax.spines[:].set_color(BORDER)
    ax1.tick_params(axis="y", colors=BLUE)
    ax2.tick_params(axis="y", colors=ORANGE)
    ax1.xaxis.set_tick_params(labelsize=8, rotation=45)
    ax1.grid(axis="y", color=BORDER, linewidth=0.5, zorder=0)

    ax1.legend(
        handles=[
            mpatches.Patch(color=BLUE, alpha=0.55, label="GDP (USD bn)"),
            mpatches.Patch(color=ORANGE, label="Remittances (USD bn)"),
        ],
        loc="upper left", fontsize=8,
        facecolor=PANEL, edgecolor=BORDER, labelcolor=TEXT, framealpha=0.9,
    )

    # ── Chart 2: Remit % of GDP ────────────────────────────────────────────
    ax3 = axes[1]
    ax3.set_facecolor(PANEL)

    pct    = df["remittance_pct_gdp"]
    colors = [GREEN if v >= 14 else BLUE for v in pct]
    ax3.bar(years, pct, color=colors, alpha=0.75, width=0.7, zorder=2)
    ax3.axhline(14, color=GREEN, linewidth=0.9, linestyle="--", alpha=0.7, zorder=3)
    ax3.text(years.iloc[0] + 0.3, 14.35, "14% threshold",
             color=GREEN, fontsize=8, alpha=0.8)

    ax3.set_xlabel("Year", color=SUBTEXT, fontsize=9)
    ax3.set_ylabel("Remittances / GDP (%)", color=SUBTEXT, fontsize=9)
    ax3.set_title("Remittances as % of GDP  2000–2024",
                  color=TEXT, fontsize=10, fontweight="bold", pad=10)
    ax3.tick_params(colors=SUBTEXT, labelsize=8)
    ax3.spines[:].set_color(BORDER)
    ax3.xaxis.set_tick_params(labelsize=8, rotation=45)
    ax3.grid(axis="y", color=BORDER, linewidth=0.5, zorder=0)

    ax3.legend(
        handles=[
            mpatches.Patch(color=GREEN, alpha=0.75, label=">= 14% of GDP"),
            mpatches.Patch(color=BLUE,  alpha=0.75, label="< 14% of GDP"),
        ],
        loc="upper left", fontsize=8,
        facecolor=PANEL, edgecolor=BORDER, labelcolor=TEXT, framealpha=0.9,
    )

    plt.tight_layout(pad=2.0)
    out = ROOT / "docs" / "preview.png"
    plt.savefig(out, dpi=160, bbox_inches="tight", facecolor=BG)
    plt.close()
    size_kb = out.stat().st_size // 1024
    print(f"Preview PNG:         {out}  ({size_kb:,} KB)")


if __name__ == "__main__":
    run_notebook()
    export_html()
    export_html_with_code()
    export_summary_dashboard()
    export_preview_png()
    print("\nDone.")
    print("  output/ph_economic_eda.html          → full notebook report")
    print("  output/summary_dashboard.html        → lightweight data card")
    print("  docs/preview.png                     → README chart image")
