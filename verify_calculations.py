"""Independent numerical checks against hand-worked analytical examples.

Run from the project root:

    python verify_calculations.py
"""

from __future__ import annotations

import math
import sys

from engineering import Fluid, LumpedBody, Pipe, PlaneWall


def assert_close(label: str, actual: float, expected: float, rel: float = 1e-3) -> None:
    """Fail the script if actual and expected differ by more than rel * |expected|."""
    tol = rel * abs(expected) if expected != 0 else rel
    ok = abs(actual - expected) <= tol
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label}: actual={actual:.6g}  expected={expected:.6g}")
    if not ok:
        raise SystemExit(1)


def main() -> None:
    """Verify pipe-flow, Fourier, and lumped-cooling examples."""
    print("1. Turbulent pipe flow — water, D=0.10 m, L=100 m, eps=0.045 mm, Q=0.010 m3/s")
    fluid = Fluid.from_preset("Water")
    pipe = Pipe(diameter=0.10, length=100.0, roughness=4.5e-5)
    q = 0.010
    area = math.pi * 0.10**2 / 4.0
    velocity = q / area
    reynolds = 998.2 * velocity * 0.10 / 1.002e-3
    rel = 4.5e-5 / 0.10
    inv_sqrt_f = -1.8 * math.log10((rel / 3.7) ** 1.11 + 6.9 / reynolds)
    friction = 1.0 / inv_sqrt_f**2
    dp = friction * (100.0 / 0.10) * (998.2 * velocity**2 / 2.0)
    result = pipe.analyse(fluid, q)

    assert_close("area m2", result.area, area)
    assert_close("velocity m/s", result.velocity, velocity)
    assert_close("Reynolds number", result.reynolds, reynolds)
    assert_close("friction factor", result.friction_factor, friction)
    assert_close("pressure drop Pa", result.pressure_drop, dp)
    print(
        f"    Hand values: V={velocity:.4f} m/s, Re={reynolds:.4e}, "
        f"f={friction:.5f}, dP={dp / 1000:.3f} kPa"
    )

    print("\n2. Laminar pipe flow — water, D=0.10 m, L=100 m, Q=1e-5 m3/s")
    q_lam = 1.0e-5
    v_lam = q_lam / area
    re_lam = 998.2 * v_lam * 0.10 / 1.002e-3
    f_lam = 64.0 / re_lam
    dp_lam = f_lam * (100.0 / 0.10) * (998.2 * v_lam**2 / 2.0)
    lam = pipe.analyse(fluid, q_lam)
    assert_close("laminar Re", lam.reynolds, re_lam)
    assert_close("laminar f = 64/Re", lam.friction_factor, f_lam)
    assert_close("laminar dP Pa", lam.pressure_drop, dp_lam)
    print(f"    Hand values: Re={re_lam:.1f} (laminar), f={f_lam:.4f}")

    print("\n3. Plane wall — k=0.80 W/m.K, L=0.20 m, A=10 m2, dT=20 K")
    wall = PlaneWall(thickness=0.20, conductivity=0.80, area=10.0)
    assert_close("heat rate W", wall.heat_rate(20.0, 0.0), 800.0)
    assert_close("heat flux W/m2", wall.heat_flux(20.0, 0.0), 80.0)
    assert_close("resistance K/W", wall.resistance, 0.025)

    print("\n4. Lumped cooling — m=1 kg, c=500, h=20, A=0.05, 80 C to 40 C in 20 C air")
    body = LumpedBody(mass=1.0, specific_heat=500.0, convection_coeff=20.0, surface_area=0.05)
    tau = 500.0
    t_star = -tau * math.log((40.0 - 20.0) / (80.0 - 20.0))
    assert_close("time constant s", body.time_constant, tau)
    assert_close("time to 40 C s", body.time_to_temperature(80.0, 20.0, 40.0), t_star)
    assert_close("T at t* C", body.temperature(t_star, 80.0, 20.0), 40.0)
    print(f"    Hand values: tau={tau:.1f} s, t*={t_star:.2f} s")
    print("\nAll verification checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
