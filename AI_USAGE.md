# AI usage log (PE 262 Module D)

Cursor (Grok) was used as a coding assistant. Every formula, unit conversion, and UI control was checked against the course brief and against independent hand calculations in `verify_calculations.py`.

## Prompt 1 — application structure

**Asked:** Scaffold a multi-page Streamlit app for a PE 262 capstone: pipe flow, heat transfer, and a rock/fluid CSV dashboard, with OOP classes in a separate `engineering.py`.

**Verified:** Page files live under `pages/`; `app.py` is the home page; `Fluid`, `Pipe`, `PlaneWall`, and `LumpedBody` are imported from `engineering.py`, not defined inside the Streamlit scripts.

**Corrected:** An early draft mixed display units (mm, L/s) into the classes. Classes now accept SI only. Millimetres and litres per second are converted in the Streamlit pages before a class is constructed.

## Prompt 2 — pipe-flow friction factor

**Asked:** Implement velocity, Reynolds number, Darcy friction factor, and pressure drop, with an interactive ΔP vs Q plot and CSV export.

**Verified:** Water worked example (D = 0.10 m, L = 100 m, ε = 0.045 mm, Q = 10 L/s) was computed by hand using Haaland + Darcy–Weisbach, then compared to `Pipe.analyse` (see `verify_calculations.py`). A second laminar case checks \(f = 64/\mathrm{Re}\). Relative error is below 0.1%.

**Corrected:** An early version used the Fanning friction factor (4× too small in ΔP). The code now uses the Darcy factor throughout. Laminar flow uses \(f = 64/\mathrm{Re}\), not the turbulent formula.

## Prompt 3 — lumped cooling and Streamlit Cloud

**Asked:** Add Newton cooling with a temperature–time plot that follows sliders, plus README / requirements for Streamlit Community Cloud.

**Verified:** Analytical solution \(t^* = -\tau \ln[(T_\mathrm{target}-T_\infty)/(T_0-T_\infty)]\) for m = 1 kg, c = 500 J/kg·K, h = 20 W/m²·K, A = 0.05 m², 80 °C → 40 °C in 20 °C air gives τ = 500 s and t* = 549.3 s. The app matches. Fourier brick-wall check \(\dot{Q} = 800\,\mathrm{W}\) also matches.

**Corrected:** The first cooling UI allowed T_target outside (T∞, T0), which makes ln of a negative ratio and would crash. `LumpedBody.time_to_temperature` now raises `EngineeringError` and the page shows the message instead of dying. `requirements.txt` lists only packages Streamlit Cloud can install (`streamlit`, `pandas`, `numpy`, `plotly`).
