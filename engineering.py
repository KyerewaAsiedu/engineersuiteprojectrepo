"""
Core engineering models for the PE 262 Fluid Flow & Heat Transfer Suite.

This module is imported by the Streamlit pages. Calculations follow standard
undergraduate fluid mechanics and heat transfer (Darcy–Weisbach, Fourier,
lumped thermal capacitance / Newton's law of cooling).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Optional


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class EngineeringError(ValueError):
    """Raised when an input is physically invalid or a result cannot be computed."""


# ---------------------------------------------------------------------------
# Fluids
# ---------------------------------------------------------------------------

# Representative properties at ~20 °C and 1 atm. Crude oil is a typical
# light-crude value (API ~35, ~10 cP) used in teaching examples.
FLUID_PRESETS: dict[str, dict[str, float | str]] = {
    "Water": {
        "density": 998.2,  # kg/m³
        "viscosity": 1.002e-3,  # Pa·s
        "note": "Liquid water at 20 °C, 1 atm",
    },
    "Air": {
        "density": 1.204,  # kg/m³
        "viscosity": 1.825e-5,  # Pa·s
        "note": "Dry air at 20 °C, 1 atm",
    },
    "Crude oil": {
        "density": 850.0,  # kg/m³
        "viscosity": 0.010,  # Pa·s  (10 cP)
        "note": "Typical light crude at 20 °C (teaching value, ~10 cP)",
    },
}


@dataclass
class Fluid:
    """Thermophysical properties of a process fluid.

    Parameters
    ----------
    name : str
        Display name of the fluid (e.g. ``\"Water\"``).
    density : float
        Mass density ρ in kg/m³. Must be positive.
    viscosity : float
        Dynamic viscosity μ in Pa·s (N·s/m²). Must be positive.
    note : str
        Optional source / temperature note shown in the UI.
    """

    name: str
    density: float
    viscosity: float
    note: str = ""

    def __post_init__(self) -> None:
        """Validate that density and viscosity are physically positive."""
        if self.density <= 0:
            raise EngineeringError("Fluid density must be greater than 0 kg/m³.")
        if self.viscosity <= 0:
            raise EngineeringError("Fluid viscosity must be greater than 0 Pa·s.")

    @classmethod
    def from_preset(cls, name: str) -> "Fluid":
        """Return a Fluid built from a named preset (Water, Air, Crude oil).

        Parameters
        ----------
        name : str
            Key in ``FLUID_PRESETS``.

        Returns
        -------
        Fluid
        """
        if name not in FLUID_PRESETS:
            raise EngineeringError(
                f"Unknown fluid preset '{name}'. Choose Water, Air, or Crude oil."
            )
        data = FLUID_PRESETS[name]
        return cls(
            name=name,
            density=float(data["density"]),
            viscosity=float(data["viscosity"]),
            note=str(data["note"]),
        )

    @classmethod
    def user_defined(cls, density: float, viscosity: float, name: str = "User-defined") -> "Fluid":
        """Build a fluid from user-supplied density and viscosity.

        Parameters
        ----------
        density : float
            Mass density in kg/m³.
        viscosity : float
            Dynamic viscosity in Pa·s.
        name : str
            Optional label.
        """
        return cls(name=name, density=density, viscosity=viscosity, note="User-defined properties")


# ---------------------------------------------------------------------------
# Pipe flow (Darcy–Weisbach)
# ---------------------------------------------------------------------------

RE_LAMINAR_MAX = 2300.0
RE_TURBULENT_MIN = 4000.0


@dataclass
class PipeFlowResult:
    """Computed hydraulic results for a single operating point.

    Attributes
    ----------
    area : float
        Internal cross-sectional area, m².
    velocity : float
        Mean velocity V = Q / A, m/s.
    reynolds : float
        Reynolds number Re = ρ V D / μ, dimensionless.
    regime : str
        ``laminar``, ``transitional``, or ``turbulent``.
    friction_factor : float
        Darcy friction factor f, dimensionless.
    pressure_drop : float
        Frictional pressure drop ΔP, Pa.
    head_loss : float
        Head loss hf = ΔP / (ρ g), m of fluid.
    """

    area: float
    velocity: float
    reynolds: float
    regime: str
    friction_factor: float
    pressure_drop: float
    head_loss: float

    def to_dict(self) -> dict:
        """Return results as a plain dictionary (for CSV export)."""
        return asdict(self)


class Pipe:
    """Circular pipe for internal flow using the Darcy–Weisbach equation.

    ΔP = f (L / D) (ρ V² / 2)

    The Darcy friction factor is:
    * laminar (Re < 2300): f = 64 / Re
    * turbulent (Re > 4000): Haaland (1983) explicit approximation of Colebrook
    * transitional: linear blend between the two limits (avoids a jump)

    Parameters
    ----------
    diameter : float
        Internal diameter D in metres. Must be positive.
    length : float
        Pipe length L in metres. Must be positive.
    roughness : float
        Absolute roughness ε in metres (e.g. 4.5e-5 m for commercial steel).
        Must be non-negative.
    """

    GRAVITY = 9.80665  # m/s²

    def __init__(self, diameter: float, length: float, roughness: float) -> None:
        """Store pipe geometry after rejecting non-physical dimensions."""
        if diameter <= 0:
            raise EngineeringError("Pipe diameter must be greater than 0 m.")
        if length <= 0:
            raise EngineeringError("Pipe length must be greater than 0 m.")
        if roughness < 0:
            raise EngineeringError("Pipe roughness cannot be negative.")
        if roughness >= diameter:
            raise EngineeringError("Roughness must be smaller than the internal diameter.")
        self.diameter = diameter
        self.length = length
        self.roughness = roughness

    @property
    def area(self) -> float:
        """Internal cross-sectional area A = π D² / 4, m²."""
        return math.pi * self.diameter**2 / 4.0

    @property
    def relative_roughness(self) -> float:
        """Relative roughness ε / D, dimensionless."""
        return self.roughness / self.diameter

    def velocity(self, volumetric_flow: float) -> float:
        """Mean velocity V = Q / A.

        Parameters
        ----------
        volumetric_flow : float
            Volumetric flow rate Q in m³/s. Must be non-negative.
        """
        if volumetric_flow < 0:
            raise EngineeringError("Flow rate cannot be negative.")
        return volumetric_flow / self.area

    def reynolds_number(self, fluid: Fluid, volumetric_flow: float) -> float:
        """Reynolds number Re = ρ V D / μ.

        Parameters
        ----------
        fluid : Fluid
            Fluid providing density and viscosity.
        volumetric_flow : float
            Volumetric flow rate Q in m³/s.
        """
        vel = self.velocity(volumetric_flow)
        return fluid.density * vel * self.diameter / fluid.viscosity

    @staticmethod
    def _regime(re: float) -> str:
        """Classify the flow regime from Reynolds number."""
        if re < RE_LAMINAR_MAX:
            return "laminar"
        if re > RE_TURBULENT_MIN:
            return "turbulent"
        return "transitional"

    @staticmethod
    def haaland_friction_factor(re: float, rel_roughness: float) -> float:
        """Haaland (1983) explicit Darcy friction factor for turbulent flow.

        1 / √f = −1.8 log10[ (ε/D / 3.7)^1.11 + 6.9 / Re ]

        Parameters
        ----------
        re : float
            Reynolds number (must be > 0).
        rel_roughness : float
            ε / D.
        """
        if re <= 0:
            raise EngineeringError("Reynolds number must be positive for Haaland.")
        argument = (rel_roughness / 3.7) ** 1.11 + 6.9 / re
        inv_sqrt_f = -1.8 * math.log10(argument)
        return 1.0 / (inv_sqrt_f**2)

    @staticmethod
    def laminar_friction_factor(re: float) -> float:
        """Poiseuille result for fully developed laminar pipe flow: f = 64 / Re."""
        if re <= 0:
            raise EngineeringError("Reynolds number must be positive.")
        return 64.0 / re

    def friction_factor(self, re: float) -> float:
        """Darcy friction factor covering laminar, transitional, and turbulent flow.

        Parameters
        ----------
        re : float
            Reynolds number. If Re ≈ 0 (no flow), returns 0.
        """
        if re <= 1e-12:
            return 0.0
        rel = self.relative_roughness
        if re < RE_LAMINAR_MAX:
            return self.laminar_friction_factor(re)
        if re > RE_TURBULENT_MIN:
            return self.haaland_friction_factor(re, rel)
        # Transitional: blend f_lam(2300) and f_turb(4000) by Re
        f_lam = self.laminar_friction_factor(RE_LAMINAR_MAX)
        f_turb = self.haaland_friction_factor(RE_TURBULENT_MIN, rel)
        weight = (re - RE_LAMINAR_MAX) / (RE_TURBULENT_MIN - RE_LAMINAR_MAX)
        return f_lam + weight * (f_turb - f_lam)

    def pressure_drop(self, fluid: Fluid, volumetric_flow: float) -> float:
        """Frictional pressure drop ΔP in Pa from Darcy–Weisbach.

        Parameters
        ----------
        fluid : Fluid
        volumetric_flow : float
            Q in m³/s.
        """
        vel = self.velocity(volumetric_flow)
        re = self.reynolds_number(fluid, volumetric_flow)
        f = self.friction_factor(re)
        return f * (self.length / self.diameter) * (fluid.density * vel**2 / 2.0)

    def analyse(self, fluid: Fluid, volumetric_flow: float) -> PipeFlowResult:
        """Compute the full hydraulic result set for one flow rate.

        Parameters
        ----------
        fluid : Fluid
        volumetric_flow : float
            Q in m³/s.
        """
        area = self.area
        vel = self.velocity(volumetric_flow)
        re = self.reynolds_number(fluid, volumetric_flow)
        regime = self._regime(re)
        f = self.friction_factor(re)
        dp = self.pressure_drop(fluid, volumetric_flow)
        head = dp / (fluid.density * self.GRAVITY) if fluid.density > 0 else 0.0
        return PipeFlowResult(
            area=area,
            velocity=vel,
            reynolds=re,
            regime=regime,
            friction_factor=f,
            pressure_drop=dp,
            head_loss=head,
        )

    def pressure_drop_curve(
        self, fluid: Fluid, q_min: float, q_max: float, n_points: int = 40
    ) -> tuple[list[float], list[float]]:
        """Return (Q, ΔP) arrays for an interactive pressure-drop vs flow plot.

        Parameters
        ----------
        fluid : Fluid
        q_min, q_max : float
            Flow-rate range in m³/s. Both must be ≥ 0 and q_max > q_min.
        n_points : int
            Number of sample points (≥ 2).
        """
        if q_min < 0 or q_max <= q_min:
            raise EngineeringError("Flow-rate range must satisfy 0 ≤ Q_min < Q_max.")
        if n_points < 2:
            raise EngineeringError("Need at least 2 points to draw a curve.")
        flows: list[float] = []
        drops: list[float] = []
        for i in range(n_points):
            q = q_min + (q_max - q_min) * i / (n_points - 1)
            flows.append(q)
            drops.append(self.pressure_drop(fluid, q))
        return flows, drops


# ---------------------------------------------------------------------------
# Heat transfer — conduction
# ---------------------------------------------------------------------------

class PlaneWall:
    """Single-layer plane wall under one-dimensional steady conduction.

    Fourier's law for a plane wall with constant k:

        Q_dot = k A (T_hot − T_cold) / L

    Heat flux (per unit area):

        q = k (T_hot − T_cold) / L

    Thermal resistance:

        R_cond = L / (k A)

    Parameters
    ----------
    thickness : float
        Wall thickness L in metres. Must be positive.
    conductivity : float
        Thermal conductivity k in W/(m·K). Must be positive.
    area : float
        Heat-transfer area A in m². Must be positive.
    """

    def __init__(self, thickness: float, conductivity: float, area: float) -> None:
        """Store wall properties after rejecting non-physical inputs."""
        if thickness <= 0:
            raise EngineeringError("Wall thickness must be greater than 0 m.")
        if conductivity <= 0:
            raise EngineeringError("Thermal conductivity must be greater than 0 W/(m·K).")
        if area <= 0:
            raise EngineeringError("Heat-transfer area must be greater than 0 m².")
        self.thickness = thickness
        self.conductivity = conductivity
        self.area = area

    @property
    def resistance(self) -> float:
        """Conduction resistance R = L / (k A) in K/W."""
        return self.thickness / (self.conductivity * self.area)

    def heat_rate(self, t_hot: float, t_cold: float) -> float:
        """Steady heat transfer rate Q_dot in watts.

        Parameters
        ----------
        t_hot, t_cold : float
            Surface temperatures in °C (or K — only the difference matters).
        """
        return self.conductivity * self.area * (t_hot - t_cold) / self.thickness

    def heat_flux(self, t_hot: float, t_cold: float) -> float:
        """Heat flux q in W/m²."""
        return self.conductivity * (t_hot - t_cold) / self.thickness


# ---------------------------------------------------------------------------
# Heat transfer — Newton's law of cooling (lumped capacitance)
# ---------------------------------------------------------------------------

class LumpedBody:
    """Lumped thermal capacitance model (Newton's law of cooling).

    Energy balance: m c dT/dt = − h A (T − T_∞)

    Solution:

        (T(t) − T_∞) / (T0 − T_∞) = exp(−t / τ)

    Time constant:

        τ = m c / (h A) = ρ V c / (h A)

    Time to reach a target temperature:

        t = −τ ln[ (T_target − T_∞) / (T0 − T_∞) ]

    Parameters
    ----------
    mass : float
        Mass m in kg. Must be positive.
    specific_heat : float
        Specific heat c in J/(kg·K). Must be positive.
    convection_coeff : float
        Convective heat-transfer coefficient h in W/(m²·K). Must be positive.
    surface_area : float
        Exposed surface area A in m². Must be positive.
    """

    def __init__(
        self,
        mass: float,
        specific_heat: float,
        convection_coeff: float,
        surface_area: float,
    ) -> None:
        """Store lumped-body properties after rejecting non-physical inputs."""
        if mass <= 0:
            raise EngineeringError("Mass must be greater than 0 kg.")
        if specific_heat <= 0:
            raise EngineeringError("Specific heat must be greater than 0 J/(kg·K).")
        if convection_coeff <= 0:
            raise EngineeringError("Convection coefficient h must be greater than 0 W/(m²·K).")
        if surface_area <= 0:
            raise EngineeringError("Surface area must be greater than 0 m².")
        self.mass = mass
        self.specific_heat = specific_heat
        self.convection_coeff = convection_coeff
        self.surface_area = surface_area

    @property
    def time_constant(self) -> float:
        """Thermal time constant τ = m c / (h A) in seconds."""
        return (self.mass * self.specific_heat) / (self.convection_coeff * self.surface_area)

    def temperature(self, t_seconds: float, t0: float, t_inf: float) -> float:
        """Temperature T(t) in °C at time t seconds.

        Parameters
        ----------
        t_seconds : float
            Elapsed time in seconds (≥ 0).
        t0 : float
            Initial temperature, °C.
        t_inf : float
            Ambient fluid temperature, °C.
        """
        if t_seconds < 0:
            raise EngineeringError("Time cannot be negative.")
        return t_inf + (t0 - t_inf) * math.exp(-t_seconds / self.time_constant)

    def time_to_temperature(self, t0: float, t_inf: float, t_target: float) -> float:
        """Time in seconds to cool (or heat) from T0 to T_target.

        Parameters
        ----------
        t0 : float
            Initial temperature, °C.
        t_inf : float
            Ambient temperature, °C.
        t_target : float
            Desired temperature, °C. Must lie strictly between T0 and T_∞.

        Returns
        -------
        float
            Time in seconds.
        """
        if abs(t0 - t_inf) < 1e-12:
            raise EngineeringError("Initial temperature already equals ambient; no cooling occurs.")
        ratio = (t_target - t_inf) / (t0 - t_inf)
        if ratio <= 0 or ratio >= 1:
            raise EngineeringError(
                "Target temperature must lie strictly between the initial temperature "
                "and the ambient temperature (the body cannot cross T_∞)."
            )
        return -self.time_constant * math.log(ratio)

    def cooling_curve(
        self,
        t0: float,
        t_inf: float,
        t_end: Optional[float] = None,
        n_points: int = 80,
    ) -> tuple[list[float], list[float]]:
        """Return (time_s, temperature_C) for plotting T vs t.

        Parameters
        ----------
        t0, t_inf : float
            Initial and ambient temperatures, °C.
        t_end : float, optional
            End time in seconds. Defaults to 5 time constants (≈ 99% of the change).
        n_points : int
            Number of sample points.
        """
        if n_points < 2:
            raise EngineeringError("Need at least 2 points to draw a curve.")
        duration = t_end if t_end is not None else 5.0 * self.time_constant
        if duration <= 0:
            raise EngineeringError("Plot duration must be greater than 0 s.")
        times: list[float] = []
        temps: list[float] = []
        for i in range(n_points):
            t = duration * i / (n_points - 1)
            times.append(t)
            temps.append(self.temperature(t, t0, t_inf))
        return times, temps
