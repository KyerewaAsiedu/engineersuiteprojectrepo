# Fluid Flow & Heat Transfer Engineering Suite

PE 262 capstone: a multi-page Streamlit application for pipe-flow hydraulics, heat transfer, and rock/fluid data screening.

**Repository:** https://github.com/KyerewaAsiedu/enigneersuiteproject

**Live app:** _pending Streamlit Community Cloud URL — see Deployment below_

## What it does

| Module | Page | Purpose |
| --- | --- | --- |
| A | Pipe Flow Analyser | Fluid picker, pipe geometry, velocity, Re, Darcy friction factor, ΔP, ΔP–Q plot, CSV export |
| B | Heat Transfer Calculator | Fourier conduction through a flat wall; lumped Newton cooling with a live T–t curve |
| C | Rock & Fluid Dashboard | CSV upload, summary stats, porosity filter, histogram + φ–k crossplot, filtered CSV download |
| D | `engineering.py` | OOP models (`Fluid`, `Pipe`, `PlaneWall`, `LumpedBody`) imported by the Streamlit pages |

## How to run locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open the URL Streamlit prints (usually http://localhost:8501). Use the **sidebar** to switch modules.

Verify the worked examples:

```bash
python verify_calculations.py
```

## Formulas

**Pipe flow (SI)**

- \(A = \pi D^2 / 4\), \(V = Q / A\), \(\mathrm{Re} = \rho V D / \mu\)
- Laminar (\(\mathrm{Re} < 2300\)): \(f = 64 / \mathrm{Re}\)
- Turbulent (\(\mathrm{Re} > 4000\)): Haaland (1983) \(1/\sqrt{f} = -1.8 \log_{10}\big[(\varepsilon/D / 3.7)^{1.11} + 6.9/\mathrm{Re}\big]\)
- Transitional: linear blend of the laminar and turbulent limits
- Darcy–Weisbach: \(\Delta P = f (L/D) \rho V^2 / 2\)

Default water example (matches the Pipe Flow sidebar): \(D=0.10\,\mathrm{m}\), \(L=100\,\mathrm{m}\), \(\varepsilon=0.045\,\mathrm{mm}\), \(Q=10\,\mathrm{L/s}\). Run `verify_calculations.py` for the exact hand values of \(V\), \(\mathrm{Re}\), \(f\), and \(\Delta P\).

**Heat transfer**

- Fourier (plane wall): \(\dot{Q} = k A \Delta T / L\). Brick check: \(k=0.80\), \(L=0.20\,\mathrm{m}\), \(A=10\,\mathrm{m^2}\), \(\Delta T=20\,\mathrm{K}\) → \(\dot{Q}=800\,\mathrm{W}\).
- Lumped cooling: \(\tau = mc/(hA)\), \(t = -\tau \ln[(T_\mathrm{target}-T_\infty)/(T_0-T_\infty)]\). Default sliders: \(m=1\,\mathrm{kg}\), \(c=500\,\mathrm{J/kg\cdot K}\), \(h=20\,\mathrm{W/m^2\cdot K}\), \(A=0.05\,\mathrm{m^2}\), \(80\to40^\circ\mathrm{C}\) in \(20^\circ\mathrm{C}\) air → \(\tau=500\,\mathrm{s}\), \(t^*=549.3\,\mathrm{s}\).

Fluid properties are at 20 °C: water 998.2 kg/m³ and 1.002×10⁻³ Pa·s; air 1.204 kg/m³ and 1.825×10⁻⁵ Pa·s; light crude 850 kg/m³ and 0.010 Pa·s.

## Project layout

```
app.py                          # home page
engineering.py                  # OOP calculation library
ui.py                           # shared page styling
pages/1_Pipe_Flow_Analyser.py
pages/2_Heat_Transfer_Calculator.py
pages/3_Rock_Fluid_Dashboard.py
data/sample_rock_fluid.csv
verify_calculations.py
AI_USAGE.md
```

## Deployment (Streamlit Community Cloud)

1. Push this repository to GitHub (public).
2. Sign in at [https://share.streamlit.io](https://share.streamlit.io) with GitHub.
3. **New app** → select this repo → branch `master` → main file `app.py` → Deploy.
4. Paste the public URL into this README (replace the placeholder at the top).

## AI assistance

Prompts, verification steps, and corrections are listed in [AI_USAGE.md](AI_USAGE.md).
