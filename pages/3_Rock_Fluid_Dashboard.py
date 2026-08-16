"""
Module C — Rock & Fluid Data Dashboard.

Upload a CSV, show summary statistics, filter (e.g. porosity above a cutoff),
plot a histogram and a porosity–permeability crossplot, download the filtered
table.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from ui import apply_page_style

st.set_page_config(page_title="Rock & Fluid Data Dashboard", page_icon="🪨", layout="wide")
apply_page_style()

SAMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_rock_fluid.csv"

st.title("Rock & Fluid Data Dashboard")
st.markdown(
    """
Load core or PVT-style tabular data, inspect it, keep only the samples that
meet a numeric cutoff, and export the filtered table. A **sample sandstone /
shale core set** is included so the page works before you upload your own file.
"""
)

st.sidebar.header("Data source")
uploaded = st.sidebar.file_uploader(
    "Upload CSV",
    type=["csv"],
    help="Any CSV with a header row. Numeric columns can be filtered and plotted.",
)
use_sample = st.sidebar.checkbox("Use built-in sample core data", value=uploaded is None)

error_message = None
df: pd.DataFrame | None = None
source_label = ""

try:
    if uploaded is not None:
        df = pd.read_csv(uploaded)
        source_label = uploaded.name
    elif use_sample:
        df = pd.read_csv(SAMPLE_PATH)
        source_label = SAMPLE_PATH.name
    else:
        df = None
except Exception as exc:  # noqa: BLE001
    error_message = f"Could not read the CSV: {exc}"

if error_message:
    st.error(error_message)
    st.stop()

if df is None or df.empty:
    st.info("Upload a CSV in the sidebar, or tick **Use built-in sample core data**.")
    st.stop()

df.columns = [str(c).strip() for c in df.columns]
numeric_cols = df.select_dtypes(include="number").columns.tolist()

st.caption(f"Loaded **{source_label}** · {len(df)} rows × {len(df.columns)} columns.")
st.subheader("Raw table")
st.dataframe(df, use_container_width=True, hide_index=True)

st.subheader("Summary statistics")
if numeric_cols:
    st.dataframe(df[numeric_cols].describe().T, use_container_width=True)
else:
    st.warning("No numeric columns were found, so statistics and charts are unavailable.")

# ---------------------------------------------------------------------------
# Filter
# ---------------------------------------------------------------------------
st.sidebar.header("Filter")
filtered = df.copy()
filter_col = None
cutoff = None

if numeric_cols:
    filter_col = st.sidebar.selectbox(
        "Filter column",
        options=numeric_cols,
        index=numeric_cols.index("porosity_pct") if "porosity_pct" in numeric_cols else 0,
        help="Rows with a value greater than the cutoff are kept.",
    )
    col_min = float(df[filter_col].min())
    col_max = float(df[filter_col].max())
    default = col_min
    if filter_col.lower().startswith("porosity"):
        default = min(max(15.0, col_min), col_max)
    cutoff = st.sidebar.slider(
        f"Keep rows where {filter_col} >",
        min_value=float(f"{col_min:.4g}"),
        max_value=float(f"{col_max:.4g}"),
        value=float(f"{default:.4g}"),
        help="Example from the brief: show only samples where porosity > X%.",
    )
    filtered = df.loc[df[filter_col] > cutoff].copy()

st.subheader("Filtered table")
if filter_col is not None:
    st.caption(f"{len(filtered)} of {len(df)} rows where **{filter_col} > {cutoff:g}**.")
st.dataframe(filtered, use_container_width=True, hide_index=True)

csv_bytes = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download filtered CSV",
    data=csv_bytes,
    file_name="filtered_rock_fluid_data.csv",
    mime="text/csv",
    disabled=filtered.empty,
)

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
st.subheader("Charts")
if filtered.empty:
    st.warning("No rows remain after filtering, so charts cannot be drawn. Lower the cutoff.")
    st.stop()

if not numeric_cols:
    st.stop()

hist_default = "porosity_pct" if "porosity_pct" in numeric_cols else numeric_cols[0]
x_default = "porosity_pct" if "porosity_pct" in numeric_cols else numeric_cols[0]
y_default = "permeability_md" if "permeability_md" in numeric_cols else (
    numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0]
)

left, right = st.columns(2)
with left:
    hist_col = st.selectbox("Histogram column", options=numeric_cols, index=numeric_cols.index(hist_default))
    fig_h = px.histogram(
        filtered,
        x=hist_col,
        nbins=12,
        color="lithology" if "lithology" in filtered.columns else None,
        title=f"Histogram of {hist_col}",
        template="plotly_white",
    )
    fig_h.update_layout(bargap=0.05, height=420, margin=dict(t=50))
    st.plotly_chart(fig_h, use_container_width=True)

with right:
    x_col = st.selectbox("Crossplot X", options=numeric_cols, index=numeric_cols.index(x_default))
    y_col = st.selectbox("Crossplot Y", options=numeric_cols, index=numeric_cols.index(y_default))
    fig_s = px.scatter(
        filtered,
        x=x_col,
        y=y_col,
        color="lithology" if "lithology" in filtered.columns else None,
        hover_data=filtered.columns.tolist(),
        title=f"{y_col} vs {x_col}",
        template="plotly_white",
        log_y=y_col.lower().startswith("perm"),
    )
    fig_s.update_traces(marker=dict(size=10))
    fig_s.update_layout(height=420, margin=dict(t=50))
    st.plotly_chart(fig_s, use_container_width=True)

st.caption(
    "Permeability is plotted on a log axis when the Y column looks like permeability "
    "(typical for core data, which often spans several orders of magnitude)."
)
