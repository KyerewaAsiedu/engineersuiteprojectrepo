"""
PE 262 Capstone — Fluid Flow & Heat Transfer Engineering Suite.

Home page for the multi-page Streamlit application. Use the sidebar to open
Pipe Flow Analyser, Heat Transfer Calculator, or Rock & Fluid Data Dashboard.
"""

import streamlit as st

from ui import apply_page_style

st.set_page_config(
    page_title="PE 262 Engineering Suite",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_page_style()

st.title("Fluid Flow & Heat Transfer Engineering Suite")
st.caption("PE 262 Capstone — a deployed engineering calculator for pipe hydraulics, heat transfer, and rock/fluid data.")

st.markdown(
    """
This application is a professional toolkit for petroleum and process-engineering
calculations. Open a module from the **sidebar**. Every formula is implemented in
`engineering.py` as documented Python classes (`Fluid`, `Pipe`, `PlaneWall`,
`LumpedBody`) and has been checked against hand-calculated analytical examples.
"""
)

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.subheader("Module A — Pipe Flow")
    st.markdown(
        """
Select a fluid, enter pipe geometry and flow rate, then read **velocity,
Reynolds number, friction factor, and pressure drop**. Plot ΔP against Q and
export the operating point to CSV.
"""
    )
    st.page_link("pages/1_Pipe_Flow_Analyser.py", label="Open Pipe Flow Analyser", icon="🌊")

with col_b:
    st.subheader("Module B — Heat Transfer")
    st.markdown(
        """
**(1)** Steady conduction through a single-layer wall (Fourier's law).
**(2)** Time to cool a lumped body (Newton's law of cooling).
**(3)** Interactive temperature–time curve with sliders.
"""
    )
    st.page_link("pages/2_Heat_Transfer_Calculator.py", label="Open Heat Transfer Calculator", icon="🔥")

with col_c:
    st.subheader("Module C — Data Dashboard")
    st.markdown(
        """
Upload a rock or fluid CSV, inspect summary statistics, filter samples
(e.g. porosity above a cutoff), plot a histogram and a porosity–permeability
crossplot, then download the filtered table.
"""
    )
    st.page_link("pages/3_Rock_Fluid_Dashboard.py", label="Open Rock & Fluid Dashboard", icon="🪨")

st.divider()
st.subheader("Formulas used")

left, right = st.columns(2)
with left:
    st.markdown(
        r"""
**Pipe flow (Darcy–Weisbach)**

$$
V = \frac{Q}{A},\quad
Re = \frac{\rho V D}{\mu},\quad
\Delta P = f\,\frac{L}{D}\,\frac{\rho V^{2}}{2}
$$

- Laminar ($Re < 2300$): $f = 64/Re$
- Turbulent ($Re > 4000$): Haaland (1983) explicit Colebrook approximation
- Transitional: linear blend of the two limits
"""
    )
with right:
    st.markdown(
        r"""
**Heat transfer**

Fourier (plane wall):

$$
\dot{Q} = k A \frac{T_\mathrm{hot}-T_\mathrm{cold}}{L}
$$

Newton / lumped cooling:

$$
\frac{T(t)-T_\infty}{T_0-T_\infty} = e^{-t/\tau},\quad
\tau = \frac{m c}{h A}
$$
"""
    )

st.divider()
st.markdown(
    """
**How to run locally**

```bash
pip install -r requirements.txt
streamlit run app.py
```

**Verification:** from the project folder run `python verify_calculations.py`.
All four analytical cases must print `PASS`.
"""
)
