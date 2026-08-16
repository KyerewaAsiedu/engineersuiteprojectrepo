"""
Module A — Pipe Flow Analyser.

Sidebar inputs for fluid, geometry, and flow rate. Metrics for velocity,
Reynolds number, friction factor, and pressure drop. Interactive ΔP vs Q
plot and CSV export of the operating point plus the curve.
"""

from __future__ import annotations

import io

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from engineering import FLUID_PRESETS, EngineeringError, Fluid, Pipe
from ui import apply_page_style

st.set_page_config(page_title="Pipe Flow Analyser", page_icon="🔧", layout="wide")
apply_page_style()

st.title("Pipe Flow Analyser")
st.markdown(
    """
Computes mean **velocity**, **Reynolds number**, **Darcy friction factor**, and
**frictional pressure drop** for steady, fully developed flow in a circular pipe
(Darcy–Weisbach). Preset fluids use properties at **20 °C, 1 atm**.
"""
)

# ---------------------------------------------------------------------------
# Sidebar inputs
# ---------------------------------------------------------------------------
st.sidebar.header("Fluid")
fluid_choice = st.sidebar.selectbox(
    "Fluid",
    options=["Water", "Air", "Crude oil", "User-defined"],
    help="Presets auto-fill density and viscosity. Choose User-defined to type your own.",
)

if fluid_choice == "User-defined":
    density = st.sidebar.number_input(
        "Density ρ (kg/m³)",
        min_value=0.01,
        value=998.2,
        format="%.4f",
        help="Mass per unit volume of the fluid.",
    )
    viscosity = st.sidebar.number_input(
        "Dynamic viscosity μ (Pa·s)",
        min_value=1e-8,
        value=1.002e-3,
        format="%.6e",
        help="1 cP = 0.001 Pa·s. Water at 20 °C is about 0.001 Pa·s.",
    )
    fluid_note = "User-defined properties"
else:
    preset = FLUID_PRESETS[fluid_choice]
    density = float(preset["density"])
    viscosity = float(preset["viscosity"])
    fluid_note = str(preset["note"])
    st.sidebar.metric("Density ρ", f"{density:g} kg/m³")
    st.sidebar.metric("Viscosity μ", f"{viscosity:g} Pa·s")
    st.sidebar.caption(fluid_note)

st.sidebar.header("Pipe geometry")
diameter_mm = st.sidebar.number_input(
    "Internal diameter D (mm)",
    min_value=0.1,
    value=100.0,
    step=1.0,
    help="Inside diameter of the pipe. 100 mm = 0.1 m.",
)
length_m = st.sidebar.number_input(
    "Length L (m)",
    min_value=0.01,
    value=100.0,
    step=1.0,
    help="Developed length over which frictional drop is calculated.",
)
roughness_mm = st.sidebar.number_input(
    "Absolute roughness ε (mm)",
    min_value=0.0,
    value=0.045,
    step=0.001,
    format="%.4f",
    help="Commercial steel ≈ 0.045 mm. Drawn tubing ≈ 0.0015 mm. Concrete ≈ 0.3–3 mm.",
)

st.sidebar.header("Operating point")
flow_unit = st.sidebar.selectbox("Flow-rate unit", ["L/s", "m³/s", "m³/h"])
if flow_unit == "L/s":
    q_input = st.sidebar.number_input("Flow rate Q (L/s)", min_value=0.0, value=10.0, step=0.1)
    q_m3s = q_input / 1000.0
elif flow_unit == "m³/h":
    q_input = st.sidebar.number_input("Flow rate Q (m³/h)", min_value=0.0, value=36.0, step=0.5)
    q_m3s = q_input / 3600.0
else:
    q_input = st.sidebar.number_input("Flow rate Q (m³/s)", min_value=0.0, value=0.010, step=0.001, format="%.5f")
    q_m3s = q_input

st.sidebar.header("ΔP vs Q plot range")
q_plot_max_ls = st.sidebar.slider(
    "Maximum flow on plot (L/s)",
    min_value=1.0,
    max_value=200.0,
    value=40.0,
    help="The curve is drawn from 0 to this flow rate.",
)

# ---------------------------------------------------------------------------
# Calculate
# ---------------------------------------------------------------------------
error_message = None
result = None
pipe = None
fluid = None

try:
    fluid = Fluid(name=fluid_choice, density=density, viscosity=viscosity, note=fluid_note)
    pipe = Pipe(
        diameter=diameter_mm / 1000.0,
        length=length_m,
        roughness=roughness_mm / 1000.0,
    )
    result = pipe.analyse(fluid, q_m3s)
except EngineeringError as exc:
    error_message = str(exc)
except Exception as exc:  # noqa: BLE001 — show any unexpected error in the UI
    error_message = f"Could not compute the result: {exc}"

if error_message:
    st.error(error_message)
    st.stop()

assert result is not None and pipe is not None and fluid is not None

regime_colour = {
    "laminar": "Normal",
    "transitional": "Off",
    "turbulent": "Inverse",
}

st.subheader("Operating point")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Velocity V", f"{result.velocity:.3f} m/s")
m2.metric("Reynolds Re", f"{result.reynolds:,.0f}")
m3.metric("Regime", result.regime.capitalize())
m4.metric("Friction factor f", f"{result.friction_factor:.5f}")
m5.metric("Pressure drop ΔP", f"{result.pressure_drop/1000.0:.3f} kPa")

c1, c2, c3 = st.columns(3)
c1.metric("Head loss hf", f"{result.head_loss:.3f} m of fluid")
c2.metric("Area A", f"{result.area:.6f} m²")
c3.metric("Relative roughness ε/D", f"{pipe.relative_roughness:.5g}")

st.caption(
    f"Fluid: **{fluid.name}** · ρ = {fluid.density:g} kg/m³ · μ = {fluid.viscosity:g} Pa·s. "
    f"{fluid.note}.  ΔP is also {result.pressure_drop:.1f} Pa "
    f"({result.pressure_drop/1e5:.4f} bar)."
)

# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
st.subheader("Pressure drop vs flow rate")
try:
    q_max_m3s = q_plot_max_ls / 1000.0
    flows, drops = pipe.pressure_drop_curve(fluid, 0.0, q_max_m3s, n_points=50)
except EngineeringError as exc:
    st.error(str(exc))
    flows, drops = [], []

fig = go.Figure()
if flows:
    fig.add_trace(
        go.Scatter(
            x=[q * 1000.0 for q in flows],
            y=[dp / 1000.0 for dp in drops],
            mode="lines",
            name="ΔP(Q)",
            line=dict(color="#0F766E", width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[q_m3s * 1000.0],
            y=[result.pressure_drop / 1000.0],
            mode="markers",
            name="Operating point",
            marker=dict(size=12, color="#C2410C"),
        )
    )
fig.update_layout(
    xaxis_title="Flow rate Q (L/s)",
    yaxis_title="Pressure drop ΔP (kPa)",
    template="plotly_white",
    height=420,
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    margin=dict(t=40, b=40),
)
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------
st.subheader("Export")

point_row = {
    "fluid": fluid.name,
    "density_kg_m3": fluid.density,
    "viscosity_Pa_s": fluid.viscosity,
    "diameter_m": pipe.diameter,
    "length_m": pipe.length,
    "roughness_m": pipe.roughness,
    "flow_m3_s": q_m3s,
    "velocity_m_s": result.velocity,
    "reynolds": result.reynolds,
    "regime": result.regime,
    "friction_factor": result.friction_factor,
    "pressure_drop_Pa": result.pressure_drop,
    "head_loss_m": result.head_loss,
}
point_df = pd.DataFrame([point_row])
curve_df = pd.DataFrame(
    {
        "flow_L_s": [q * 1000.0 for q in flows],
        "pressure_drop_kPa": [dp / 1000.0 for dp in drops],
    }
)

tab_point, tab_curve = st.tabs(["Operating point CSV", "Curve CSV"])
with tab_point:
    st.dataframe(point_df, use_container_width=True, hide_index=True)
    st.download_button(
        "Download operating point CSV",
        data=point_df.to_csv(index=False).encode("utf-8"),
        file_name="pipe_flow_operating_point.csv",
        mime="text/csv",
    )
with tab_curve:
    st.dataframe(curve_df, use_container_width=True, hide_index=True)
    buffer = io.StringIO()
    curve_df.to_csv(buffer, index=False)
    st.download_button(
        "Download ΔP vs Q curve CSV",
        data=buffer.getvalue().encode("utf-8"),
        file_name="pipe_flow_deltaP_vs_Q.csv",
        mime="text/csv",
    )

with st.expander("Worked verification example (turbulent water)"):
    st.markdown(
        r"""
Hand check used in `verify_calculations.py`: water, **D = 100 mm**, **L = 100 m**,
**ε = 0.045 mm**, **Q = 10 L/s**.

1. $A = \pi D^2/4 = 7.854\times 10^{-3}\,\mathrm{m}^2$
2. $V = Q/A = 1.273\,\mathrm{m/s}$
3. $Re = \rho V D / \mu = 1.268\times 10^5$ (turbulent)
4. Haaland $f = 0.01927$, then $\Delta P = f (L/D) \rho V^2/2 = 15.59\,\mathrm{kPa}$

Set the sidebar to these values and confirm the metrics match the verification script.
"""
    )
