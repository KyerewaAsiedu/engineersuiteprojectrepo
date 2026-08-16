"""
Module B — Heat Transfer Calculator.

(1) Steady conduction through a single-layer plane wall (Fourier's law).
(2) Time to cool a lumped body (Newton's law of cooling).
(3) Interactive T vs t curve driven by sliders.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from engineering import EngineeringError, LumpedBody, PlaneWall
from ui import apply_page_style

st.set_page_config(page_title="Heat Transfer Calculator", page_icon="🔥", layout="wide")
apply_page_style()

st.title("Heat Transfer Calculator")
st.markdown(
    """
Two independent calculators. **Conduction** is a steady energy flow through a
flat wall. **Cooling** is a transient energy balance on a solid that is
well-mixed internally (the lumped-capacitance / Newton's-law-of-cooling model).
"""
)

tab_wall, tab_cool = st.tabs(["1. Plane-wall conduction", "2. Newton's law of cooling"])

# ===========================================================================
# Tab 1 — Fourier
# ===========================================================================
with tab_wall:
    st.subheader("Steady conduction through a flat wall")
    st.markdown(
        r"""
Fourier's law for one-dimensional conduction with constant thermal conductivity:

$$
\dot{Q} = k A \frac{T_\mathrm{hot} - T_\mathrm{cold}}{L}
\qquad
q = \frac{\dot{Q}}{A} = k \frac{\Delta T}{L}
\qquad
R_\mathrm{cond} = \frac{L}{k A}
$$

This is a **single layer** (one material). Heat rate is positive when the hot
face is warmer than the cold face.
"""
    )

    c1, c2 = st.columns(2)
    with c1:
        thickness = st.number_input(
            "Wall thickness L (m)",
            min_value=1e-4,
            value=0.20,
            step=0.01,
            format="%.4f",
            help="Distance between the two faces. Brick / insulation examples often use 0.05–0.3 m.",
        )
        conductivity = st.number_input(
            "Thermal conductivity k (W/(m·K))",
            min_value=1e-4,
            value=0.80,
            step=0.05,
            format="%.4f",
            help="Brick ≈ 0.6–1.0, window glass ≈ 1.0, carbon steel ≈ 40–50, copper ≈ 400, mineral wool ≈ 0.04.",
        )
        area = st.number_input(
            "Heat-transfer area A (m²)",
            min_value=1e-4,
            value=10.0,
            step=0.5,
            help="Face area through which heat flows (width × height of the wall).",
        )
    with c2:
        t_hot = st.number_input(
            "Hot-face temperature T_hot (°C)",
            value=20.0,
            step=1.0,
            help="Temperature of the warmer surface. Units °C; only the difference from T_cold matters.",
        )
        t_cold = st.number_input(
            "Cold-face temperature T_cold (°C)",
            value=0.0,
            step=1.0,
            help="Temperature of the cooler surface.",
        )
        st.caption("Typical k: air 0.026 · water 0.60 · sandstone 1.5–2.5 · steel 45 · copper 400 W/(m·K).")

    try:
        wall = PlaneWall(thickness=thickness, conductivity=conductivity, area=area)
        q_dot = wall.heat_rate(t_hot, t_cold)
        flux = wall.heat_flux(t_hot, t_cold)
        r_cond = wall.resistance
    except EngineeringError as exc:
        st.error(str(exc))
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not compute conduction: {exc}")
    else:
        m1, m2, m3 = st.columns(3)
        m1.metric("Heat rate Q̇", f"{q_dot:.2f} W")
        m2.metric("Heat flux q", f"{flux:.2f} W/m²")
        m3.metric("Resistance R_cond", f"{r_cond:.5f} K/W")
        st.caption(
            "Check: Q̇ must equal ΔT / R. "
            f"ΔT = {t_hot - t_cold:.2f} K, so ΔT / R = {(t_hot - t_cold) / r_cond:.2f} W."
        )
        with st.expander("Hand-calculated check (brick wall)"):
            st.markdown(
                """
k = 0.80 W/(m·K), A = 10 m², L = 0.20 m, T_hot = 20 °C, T_cold = 0 °C:

Q̇ = 0.80 × 10 × 20 / 0.20 = **800 W**,  q = **80 W/m²**,  R = **0.025 K/W**.
"""
            )

# ===========================================================================
# Tab 2 — Newton's law of cooling
# ===========================================================================
with tab_cool:
    st.subheader("Time to cool (lumped thermal capacitance)")
    st.markdown(
        r"""
Newton's law of cooling: the surface heat loss is \(h A (T - T_\infty)\).
If the solid is nearly uniform in temperature (Biot number \(Bi = h(V/A)/k \ll 1\)),
the energy balance integrates to

$$
\frac{T(t) - T_\infty}{T_0 - T_\infty} = \exp\left(-\frac{t}{\tau}\right),
\qquad
\tau = \frac{m c}{h A}
$$

Time to a target temperature (must lie **between** \(T_0\) and \(T_\infty\)):

$$
t = -\tau \ln\left(\frac{T_\mathrm{target} - T_\infty}{T_0 - T_\infty}\right)
$$
"""
    )

    st.markdown("**Geometry / material** — drag sliders; the plot updates immediately.")
    col_g, col_t = st.columns(2)
    with col_g:
        mass = st.slider(
            "Mass m (kg)",
            min_value=0.05,
            max_value=20.0,
            value=1.0,
            step=0.05,
            help="Mass of the object being cooled. Steel slug examples often use 0.5–5 kg.",
        )
        specific_heat = st.slider(
            "Specific heat c (J/(kg·K))",
            min_value=100.0,
            max_value=5000.0,
            value=500.0,
            step=10.0,
            help="Energy to raise 1 kg by 1 K. Steel ≈ 450–500, aluminium ≈ 900, water ≈ 4180 J/(kg·K).",
        )
        h_conv = st.slider(
            "Convection coefficient h (W/(m²·K))",
            min_value=1.0,
            max_value=200.0,
            value=20.0,
            step=1.0,
            help="Natural convection in air ≈ 5–25. Forced air ≈ 20–100. Water ≈ 100–1000.",
        )
        surface_area = st.slider(
            "Surface area A (m²)",
            min_value=0.005,
            max_value=1.0,
            value=0.05,
            step=0.005,
            help="Area exposed to the ambient fluid. A 10 cm cube has A ≈ 0.06 m².",
        )
    with col_t:
        t0 = st.slider(
            "Initial temperature T₀ (°C)",
            min_value=-20.0,
            max_value=300.0,
            value=80.0,
            step=1.0,
            help="Temperature of the body at t = 0.",
        )
        t_inf = st.slider(
            "Ambient temperature T∞ (°C)",
            min_value=-20.0,
            max_value=80.0,
            value=20.0,
            step=1.0,
            help="Far-field fluid temperature surrounding the body.",
        )
        t_target = st.slider(
            "Target temperature T_target (°C)",
            min_value=-20.0,
            max_value=300.0,
            value=40.0,
            step=1.0,
            help="Must lie strictly between T₀ and T∞. For cooling, T∞ < T_target < T₀.",
        )

    try:
        body = LumpedBody(
            mass=mass,
            specific_heat=specific_heat,
            convection_coeff=h_conv,
            surface_area=surface_area,
        )
        tau = body.time_constant
        t_req = body.time_to_temperature(t0=t0, t_inf=t_inf, t_target=t_target)
        times, temps = body.cooling_curve(t0=t0, t_inf=t_inf, t_end=max(5.0 * tau, t_req * 1.2))
        t_now = body.temperature(t_req, t0, t_inf)
    except EngineeringError as exc:
        st.error(str(exc))
        st.info(
            "For cooling, choose T_target between T∞ and T₀. "
            "Example: T₀ = 80 °C, T∞ = 20 °C, T_target = 40 °C."
        )
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not compute cooling: {exc}")
    else:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Time constant τ", f"{tau:.1f} s")
        k2.metric("Time to target", f"{t_req:.1f} s")
        k3.metric("Time to target", f"{t_req/60.0:.2f} min")
        k4.metric("T at that instant", f"{t_now:.2f} °C")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=[t / 60.0 for t in times],
                y=temps,
                mode="lines",
                name="T(t)",
                line=dict(color="#C2410C", width=3),
            )
        )
        fig.add_hline(y=t_inf, line_dash="dash", line_color="#64748B", annotation_text="T∞")
        fig.add_hline(y=t_target, line_dash="dot", line_color="#0F766E", annotation_text="T_target")
        fig.add_trace(
            go.Scatter(
                x=[t_req / 60.0],
                y=[t_target],
                mode="markers",
                name="Target reached",
                marker=dict(size=12, color="#0F766E"),
            )
        )
        fig.update_layout(
            xaxis_title="Time (minutes)",
            yaxis_title="Temperature (°C)",
            template="plotly_white",
            height=440,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            margin=dict(t=40, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Hand-calculated check (steel slug)"):
            st.markdown(
                """
m = 1 kg, c = 500 J/(kg·K), h = 20 W/(m²·K), A = 0.05 m²,
T₀ = 80 °C, T∞ = 20 °C, T_target = 40 °C.

τ = 500 / (20 × 0.05) = **500 s**.  
t = −500 ln((40−20)/(80−20)) = 500 ln 3 = **549.3 s** (9.16 min).
"""
            )
