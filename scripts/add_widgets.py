"""
Inject an interactive ipywidgets section into ph_economic_eda.ipynb.
Adds Section 9 — Interactive Explorer immediately before the Key Findings cell.

Run: python scripts/add_widgets.py
"""

import json
import secrets
import sys
from pathlib import Path

NB_PATH = Path(__file__).parent.parent / "notebooks" / "ph_economic_eda.ipynb"


def md(source: str) -> dict:
    return {"cell_type": "markdown", "id": secrets.token_hex(4), "metadata": {}, "source": source.strip()}


def code(source: str, tags: list[str] | None = None) -> dict:
    meta = {}
    if tags:
        meta["tags"] = tags
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": secrets.token_hex(4),
        "metadata": meta,
        "outputs": [],
        "source": source.strip(),
    }


WIDGET_CELLS = [

    md("""
## 9. Interactive explorer

Four live widgets powered by `ipywidgets` + Plotly. Every control updates
the chart instantly — no cell re-run needed.

> **Tip:** If widgets show as static in VS Code, run the notebook in
> classic Jupyter or JupyterLab with the ipywidgets extension enabled.
"""),

    # ── Widget 0: setup ────────────────────────────────────────────────────
    code("""
import ipywidgets as widgets
from IPython.display import display, clear_output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

print("ipywidgets", widgets.__version__)
print("Widgets ready — run each cell below to launch a control panel.")
"""),

    # ── Widget 1: GDP + Remittances year-range explorer ────────────────────
    code("""
# ── Widget 1: GDP & Remittances time-range explorer ────────────────────────
# Slider controls start/end year; dropdown picks the series to highlight.

w_year_range = widgets.IntRangeSlider(
    value=[2005, 2024],
    min=int(gdp["period_year"].min()),
    max=int(gdp["period_year"].max()),
    step=1,
    description="Year range:",
    style={"description_width": "90px"},
    layout=widgets.Layout(width="520px"),
)

w_highlight = widgets.Dropdown(
    options=["None", "GFC 2009", "COVID-19 2020", "High growth (>6%)"],
    value="None",
    description="Highlight:",
    style={"description_width": "90px"},
    layout=widgets.Layout(width="280px"),
)

out1 = widgets.Output()

def render_gdp_remit(yr_range, highlight):
    yr_min, yr_max = yr_range
    g = gdp[(gdp["period_year"] >= yr_min) & (gdp["period_year"] <= yr_max)].copy()
    r = remit[(remit["period_year"] >= yr_min) & (remit["period_year"] <= yr_max)].copy()

    # Bar color logic
    def bar_color(row):
        yr = row["period_year"]
        gp = row.get("gdp_growth_pct", 0) or 0
        if highlight == "GFC 2009" and yr == 2009:
            return "#E24B4A"
        if highlight == "COVID-19 2020" and yr == 2020:
            return "#E24B4A"
        if highlight == "High growth (>6%)" and gp >= 6:
            return "#1D9E75"
        return "#85B7EB"

    colors = [bar_color(row) for _, row in g.iterrows()]

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=[
            f"GDP at current prices (USD B)  ·  {yr_min}–{yr_max}",
            f"OFW remittances (USD B)  ·  {yr_min}–{yr_max}",
        ],
    )

    fig.add_trace(go.Bar(
        x=g["period_year"], y=g["gdp_usd_bn"],
        marker_color=colors, name="GDP",
        hovertemplate="<b>%{x}</b><br>GDP: $%{y:.1f}B<extra></extra>",
    ), row=1, col=1)

    if "gdp_growth_pct" in g.columns:
        fig.add_trace(go.Scatter(
            x=g["period_year"], y=g["gdp_growth_pct"],
            mode="lines+markers", name="Growth %",
            line=dict(color="#185FA5", width=1.5), marker=dict(size=5),
            yaxis="y3",
            hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
        ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=r["period_year"], y=r["remittance_usd_bn"],
        marker_color="#9FE1CB", name="Remittances",
        hovertemplate="<b>%{x}</b><br>$%{y:.1f}B<extra></extra>",
    ), row=1, col=2)

    if "remittance_pct_gdp" in r.columns:
        fig.add_trace(go.Scatter(
            x=r["period_year"], y=r["remittance_pct_gdp"],
            mode="lines+markers", name="% of GDP",
            line=dict(color="#0F6E56", width=1.5), marker=dict(size=5),
            yaxis="y4",
            hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
        ), row=1, col=2)

    fig.update_layout(
        height=380, showlegend=False,
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=40, r=40, t=60, b=40), font=dict(size=11),
    )
    fig.update_yaxes(title_text="USD billions", row=1, col=1)
    fig.update_yaxes(title_text="USD billions", row=1, col=2)
    fig.show()

def on_change1(_):
    with out1:
        clear_output(wait=True)
        render_gdp_remit(w_year_range.value, w_highlight.value)

w_year_range.observe(on_change1, names="value")
w_highlight.observe(on_change1, names="value")

controls1 = widgets.HBox([w_year_range, w_highlight])
display(controls1, out1)
render_gdp_remit(w_year_range.value, w_highlight.value)
"""),

    # ── Widget 2: CPI inflation filter ────────────────────────────────────
    code("""
# ── Widget 2: CPI monthly inflation — year filter + BSP band toggle ────────

w_cpi_years = widgets.IntRangeSlider(
    value=[2010, 2024],
    min=2000, max=2024, step=1,
    description="Year range:",
    style={"description_width": "90px"},
    layout=widgets.Layout(width="520px"),
)

w_show_band = widgets.Checkbox(
    value=True, description="Show BSP target band (2–4%)",
    style={"description_width": "200px"},
)

w_smooth = widgets.Dropdown(
    options=["None", "3-month MA", "6-month MA", "12-month MA"],
    value="None",
    description="Smoothing:",
    style={"description_width": "90px"},
    layout=widgets.Layout(width="240px"),
)

out2 = widgets.Output()

def render_cpi(yr_range, show_band, smooth):
    yr_min, yr_max = yr_range
    c = cpi[
        (cpi["period_date"].dt.year >= yr_min) &
        (cpi["period_date"].dt.year <= yr_max)
    ].dropna(subset=["inflation_pct"]).copy()

    fig = go.Figure()

    # Raw series
    fig.add_trace(go.Scatter(
        x=c["period_date"], y=c["inflation_pct"],
        mode="lines", name="Inflation %",
        line=dict(color="#B5D4F4", width=1),
        hovertemplate="%{x|%Y-%m}: %{y:.1f}%<extra></extra>",
    ))

    # Smoothed overlay
    if smooth != "None":
        window = {"3-month MA": 3, "6-month MA": 6, "12-month MA": 12}[smooth]
        c["smoothed"] = c["inflation_pct"].rolling(window, center=True).mean()
        fig.add_trace(go.Scatter(
            x=c["period_date"], y=c["smoothed"],
            mode="lines", name=smooth,
            line=dict(color="#185FA5", width=2.5),
            hovertemplate="%{x|%Y-%m}: %{y:.1f}%<extra></extra>",
        ))

    # BSP band
    if show_band:
        fig.add_hrect(
            y0=2, y1=4,
            fillcolor="rgba(29,158,117,0.10)",
            line=dict(color="rgba(29,158,117,0.4)", width=0.8, dash="dot"),
            annotation_text="BSP 2–4%",
            annotation_position="top right",
            annotation_font_size=11,
        )
        fig.add_hline(y=0, line_color="#D3D1C7", line_width=0.8)

    # Stats annotation
    above = (c["inflation_pct"] > 4).mean() * 100
    on_target = ((c["inflation_pct"] >= 2) & (c["inflation_pct"] <= 4)).mean() * 100
    below = (c["inflation_pct"] < 2).mean() * 100

    fig.add_annotation(
        x=0.01, y=0.97, xref="paper", yref="paper",
        text=(f"Above target: {above:.0f}%  |  "
              f"On target: {on_target:.0f}%  |  "
              f"Below: {below:.0f}%"),
        showarrow=False, font=dict(size=11, color="#185FA5"),
        align="left",
    )

    fig.update_layout(
        title=f"Monthly CPI Inflation (YoY %)  ·  {yr_min}–{yr_max}",
        height=360, plot_bgcolor="white", paper_bgcolor="white",
        font=dict(size=11), margin=dict(l=40, r=40, t=60, b=40),
        showlegend=smooth != "None",
        legend=dict(orientation="h", y=-0.15),
        yaxis=dict(title="Inflation %", ticksuffix="%"),
    )
    fig.show()

def on_change2(_):
    with out2:
        clear_output(wait=True)
        render_cpi(w_cpi_years.value, w_show_band.value, w_smooth.value)

for w in [w_cpi_years, w_show_band, w_smooth]:
    w.observe(on_change2, names="value")

controls2 = widgets.VBox([
    widgets.HBox([w_cpi_years, w_smooth]),
    w_show_band,
])
display(controls2, out2)
render_cpi(w_cpi_years.value, w_show_band.value, w_smooth.value)
"""),

    # ── Widget 3: Correlation heatmap ──────────────────────────────────────
    code("""
# ── Widget 3: Correlation explorer — pick variables, Pearson vs Spearman ───

all_cols = {
    "GDP (USD B)":          "gdp_usd_bn",
    "GDP growth %":         "gdp_growth_pct",
    "GDP per capita":       "gdp_per_capita_usd",
    "Avg inflation %":      "avg_inflation_pct",
    "Remittances (USD B)":  "remittance_usd_bn",
    "Remit YoY %":          "remittance_yoy_pct",
    "Remit / GDP %":        "remittance_pct_gdp",
}

w_vars = widgets.SelectMultiple(
    options=list(all_cols.keys()),
    value=["GDP growth %", "Avg inflation %", "Remittances (USD B)", "Remit YoY %"],
    description="Variables:",
    style={"description_width": "80px"},
    layout=widgets.Layout(height="160px", width="360px"),
)

w_corr_method = widgets.RadioButtons(
    options=["Pearson", "Spearman"],
    value="Pearson",
    description="Method:",
    style={"description_width": "80px"},
)

w_corr_years = widgets.IntRangeSlider(
    value=[2000, 2024], min=2000, max=2024, step=1,
    description="Years:",
    style={"description_width": "80px"},
    layout=widgets.Layout(width="400px"),
)

out3 = widgets.Output()

def render_corr(selected_labels, method, yr_range):
    if len(selected_labels) < 2:
        with out3:
            clear_output(wait=True)
            print("Select at least 2 variables.")
        return

    yr_min, yr_max = yr_range
    sub = dash[
        (dash["period_year"] >= yr_min) &
        (dash["period_year"] <= yr_max)
    ].copy()
    cols = [all_cols[lbl] for lbl in selected_labels if all_cols[lbl] in sub.columns]
    labels = [lbl for lbl in selected_labels if all_cols[lbl] in sub.columns]
    sub = sub[cols].dropna()

    if method == "Pearson":
        corr_matrix = sub.corr(method="pearson")
    else:
        corr_matrix = sub.corr(method="spearman")

    fig = go.Figure(go.Heatmap(
        z=corr_matrix.values.tolist(),
        x=labels, y=labels,
        colorscale=[
            [0.0, "#E24B4A"],
            [0.5, "#F1EFE8"],
            [1.0, "#185FA5"],
        ],
        zmid=0, zmin=-1, zmax=1,
        text=[[f"{v:.2f}" for v in row] for row in corr_matrix.values.tolist()],
        texttemplate="%{text}",
        textfont=dict(size=13, color="#2C2C2A"),
        colorbar=dict(title="r", thickness=14),
        hovertemplate="%{y} × %{x}<br>%s r = %%{z:.3f}<extra></extra>" % method,
    ))
    fig.update_layout(
        title=f"{method} correlation matrix  ·  {yr_min}–{yr_max}  "
              f"(n={len(sub)} years)",
        height=max(300, len(labels) * 70 + 120),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(size=12), margin=dict(l=120, r=60, t=60, b=80),
        xaxis=dict(tickangle=-30),
    )
    fig.show()

def on_change3(_):
    with out3:
        clear_output(wait=True)
        render_corr(w_vars.value, w_corr_method.value, w_corr_years.value)

for w in [w_vars, w_corr_method, w_corr_years]:
    w.observe(on_change3, names="value")

controls3 = widgets.HBox([
    widgets.VBox([w_vars]),
    widgets.VBox([w_corr_method, w_corr_years]),
])
display(controls3, out3)
render_corr(w_vars.value, w_corr_method.value, w_corr_years.value)
"""),

    # ── Widget 4: Forecast horizon slider ─────────────────────────────────
    code("""
# ── Widget 4: SARIMAX remittance forecast — adjustable horizon + CI level ──

w_horizon = widgets.IntSlider(
    value=3, min=1, max=8, step=1,
    description="Forecast years:",
    style={"description_width": "120px"},
    layout=widgets.Layout(width="440px"),
)

w_ci = widgets.SelectionSlider(
    options=[("80%", 0.20), ("90%", 0.10), ("95%", 0.05), ("99%", 0.01)],
    value=0.05,
    description="CI level:",
    style={"description_width": "120px"},
    layout=widgets.Layout(width="360px"),
)

w_train_end = widgets.IntSlider(
    value=2021, min=2010, max=2022, step=1,
    description="Train until:",
    style={"description_width": "120px"},
    layout=widgets.Layout(width="440px"),
)

out4 = widgets.Output()

def render_forecast(horizon, alpha, train_end):
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from statsmodels.tools.eval_measures import rmse as calc_rmse

    rs = remit.sort_values("period_year").dropna(subset=["remittance_usd_bn"])
    ts = pd.Series(
        rs["remittance_usd_bn"].values,
        index=pd.date_range(
            start=str(int(rs["period_year"].min())),
            periods=len(rs), freq="YS",
        ),
    )

    train = ts[ts.index.year <= train_end]
    test  = ts[ts.index.year > train_end]

    try:
        model  = SARIMAX(train, order=(1,1,1), trend="t",
                         enforce_stationarity=False, enforce_invertibility=False)
        fitted = model.fit(disp=False)
        steps  = len(test) + horizon
        fc     = fitted.get_forecast(steps=steps)
        fc_m   = fc.predicted_mean
        fc_ci  = fc.conf_int(alpha=alpha)
    except Exception as exc:
        with out4:
            clear_output(wait=True)
            print(f"Model error: {exc}")
        return

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=train.index, y=train.values,
        name="Training data", marker_color="#B5D4F4",
        hovertemplate="%{x|%Y}: $%{y:.1f}B<extra></extra>",
    ))
    if len(test):
        fig.add_trace(go.Scatter(
            x=test.index, y=test.values,
            mode="markers+lines", name="Actual (holdout)",
            line=dict(color="#1D9E75", width=2),
            marker=dict(size=8, symbol="circle"),
            hovertemplate="%{x|%Y}: $%{y:.1f}B<extra></extra>",
        ))

    fig.add_trace(go.Scatter(
        x=fc_m.index, y=fc_m.values,
        mode="lines+markers", name="Forecast",
        line=dict(color="#E24B4A", width=2.5, dash="dash"),
        marker=dict(size=7, symbol="square"),
        hovertemplate="%{x|%Y}: $%{y:.1f}B<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=list(fc_ci.index) + list(fc_ci.index[::-1]),
        y=list(fc_ci.iloc[:, 1]) + list(fc_ci.iloc[::-1, 0]),
        fill="toself", fillcolor="rgba(226,75,74,0.12)",
        line=dict(color="rgba(0,0,0,0)"),
        name=f"{int((1-alpha)*100)}% CI", showlegend=True,
        hoverinfo="skip",
    ))

    # RMSE annotation
    if len(test):
        actual_vals = test.values[:min(len(test), len(fc_m))]
        fc_vals     = fc_m.values[:len(actual_vals)]
        holdout_rmse = round(
            float(np.sqrt(
                np.mean((actual_vals - fc_vals) ** 2)
            )), 2
        )
        fig.add_annotation(
            x=0.02, y=0.96, xref="paper", yref="paper",
            text=f"Holdout RMSE: ${holdout_rmse:.1f}B",
            showarrow=False, font=dict(size=11, color="#E24B4A"),
            bgcolor="rgba(255,255,255,0.8)",
        )

    ci_pct = int((1 - alpha) * 100)
    fig.update_layout(
        title=(f"OFW Remittance Forecast  ·  "
               f"Trained to {train_end}  ·  "
               f"{horizon}-year horizon  ·  {ci_pct}% CI"),
        height=400,
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(size=11),
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", y=-0.18),
        yaxis=dict(title="USD billions", tickprefix="$", ticksuffix="B"),
    )
    fig.show()

    # Forecast table below chart
    print(f"\\nForecast values ({ci_pct}% CI):")
    future_fc  = fc_m[fc_m.index.year > max(ts.index.year if len(test)==0 else test.index.year, train_end)]
    future_ci  = fc_ci.loc[future_fc.index]
    for yr_idx, (val, lo, hi) in zip(
        future_fc.index,
        zip(future_fc.values, future_ci.iloc[:,0].values, future_ci.iloc[:,1].values)
    ):
        print(f"  {yr_idx.year}: ${val:.1f}B  [{ci_pct}% CI: ${lo:.1f}B – ${hi:.1f}B]")

def on_change4(_):
    with out4:
        clear_output(wait=True)
        render_forecast(w_horizon.value, w_ci.value, w_train_end.value)

for w in [w_horizon, w_ci, w_train_end]:
    w.observe(on_change4, names="value")

controls4 = widgets.VBox([
    widgets.HBox([w_horizon, w_train_end]),
    w_ci,
])
display(controls4, out4)
render_forecast(w_horizon.value, w_ci.value, w_train_end.value)
"""),

]

# ── Inject into notebook ───────────────────────────────────────────────────────

# Finding 6: enforce script ordering — fail clearly if notebook not built yet
if not NB_PATH.exists():
    print(f"Notebook not found: {NB_PATH}")
    print("Run `python scripts/build_notebook.py` first.")
    sys.exit(1)

nb = json.loads(NB_PATH.read_text(encoding="utf-8"))

# Finding 1: idempotency guard — skip if Section 9 already present
for cell in nb["cells"]:
    if cell["cell_type"] == "markdown" and "## 9. Interactive explorer" in cell["source"]:
        print("Section 9 already present — skipping injection.")
        print("Delete Section 9 cells manually or re-run build_notebook.py to reset.")
        sys.exit(0)

# Find the index of the Key Findings cell (## 8.)
insert_idx = None
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "markdown" and "## 8. Key findings" in cell["source"]:
        insert_idx = i
        break

# Finding 6: hard exit if insertion target missing — don't silently inject in wrong position
if insert_idx is None:
    print("Error: '## 8. Key findings' cell not found in notebook.")
    print("Verify build_notebook.py produced the expected notebook structure.")
    sys.exit(1)

for j, cell in enumerate(WIDGET_CELLS):
    nb["cells"].insert(insert_idx + j, cell)

# Finding 2: atomic write — tmp file + replace to prevent partial-write corruption
tmp = NB_PATH.with_suffix(".ipynb.tmp")
tmp.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
tmp.replace(NB_PATH)  # atomic on POSIX; near-atomic on Windows

code_cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
md_cells   = [c for c in nb["cells"] if c["cell_type"] == "markdown"]
print(f"Notebook updated: {NB_PATH}")
print(f"  Total cells : {len(nb['cells'])}  ({len(code_cells)} code, {len(md_cells)} markdown)")
print(f"  Inserted at : index {insert_idx} (before Key Findings)")
print(f"  Added       : {len(WIDGET_CELLS)} cells (1 md + 5 code)")
