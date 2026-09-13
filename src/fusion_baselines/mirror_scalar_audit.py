"""Independent scalar adaptive action path; no Cartesian producer imports."""

import math
import warnings

from scipy.integrate import quad
from scipy.optimize import brentq


def scalar_action(psi, bstar, *, record=None):
    result = {} if record is None else record
    result.update(psi=psi, bstar=bstar, status="running", integrals={}, warnings=[])
    if not math.isfinite(psi) or psi <= 0 or not math.isfinite(bstar) or bstar <= 1:
        raise ValueError("finite positive flux and trapped pitch required")
    calls = dict(root=0, action=0, transit_length=0, action_psi=0)
    result["calls"] = calls

    def geometry(z):
        s = 1 + 0.7 * z * z
        r = math.sqrt(2 * psi / s)
        tangent = -0.7 * z * r / s
        length = math.sqrt(1 + tangent * tangent)
        magnitude = math.hypot(s, 0.7 * z * r)
        return s, length, magnitude

    def root_function(z):
        calls["root"] += 1
        return geometry(z)[2] - bstar

    try:
        zb = brentq(
            root_function,
            0,
            math.sqrt((bstar - 1) / 0.7),
            xtol=5e-15,
            rtol=4 * math.ulp(1.0),
        )
    except Exception as error:
        result.update(status="error", error=f"{type(error).__name__}: {error}")
        raise
    result["turning_point_z"] = zb
    integrals, caught = result["integrals"], result["warnings"]
    for name in ("action", "transit_length", "action_psi"):

        def integrand(u, name=name):
            calls[name] += 1
            z = zb * math.sin(u)
            s, length, magnitude = geometry(z)
            q = 1 - magnitude / bstar
            if q <= 0:
                raise ValueError("adaptive node outside open bounce interval")
            root_q = math.sqrt(q)
            jac = zb * math.cos(u)
            if name == "action":
                return root_q * length * jac
            if name == "transit_length":
                return length * jac / root_q
            b_psi = 0.49 * z * z / (s * magnitude)
            return (root_q * b_psi / s - length * b_psi / (2 * bstar * root_q)) * jac

        messages = []
        try:
            with warnings.catch_warnings(record=True) as messages:
                warnings.simplefilter("always")
                value, estimate = quad(
                    integrand, -math.pi / 2, math.pi / 2, epsabs=1e-10, epsrel=1e-10, limit=200
                )
        except Exception as error:
            result.update(
                status="error", error=f"{type(error).__name__}: {error}", failed_integral=name
            )
            raise
        finally:
            caught.extend(dict(integral=name, message=str(w.message)) for w in messages)
        integrals[name] = dict(value=value, absolute_error_estimate=estimate)
    result["status"] = "completed"
    return result


def relative(a, b):
    if not math.isfinite(a) or not math.isfinite(b):
        raise ValueError("finite audit values required")
    return abs(a - b) / max(abs(b), 1e-30)


def audit_values(cell, scalar, differences):
    v = cell["values"]
    checks = dict(
        scalar_source=cell["psi"] == scalar["psi"] and cell["bstar"] == scalar["bstar"],
        scalar_warnings=not scalar["warnings"],
        radial_zero=abs(v["delta_psi_reduced"]) <= 1e-10,
        direct_action=relative(v["delta_alpha_reduced"], -v["action_psi"]) <= 1e-8,
        root=relative(cell["turning_point_z"], scalar["turning_point_z"]) <= 1e-12,
    )
    errors = {}
    for name, target, sign in (
        ("action", "action", 1),
        ("transit_length", "transit_length", 1),
        ("delta_alpha_reduced", "action_psi", -1),
    ):
        errors[name] = relative(v[name], sign * scalar["integrals"][target]["value"])
        checks[f"scalar_{name}"] = errors[name] <= 1e-7
    checks["both_fixed_fd_scales"] = [d["relative_step"] for d in differences] == [1e-4, 1e-5]
    for i, difference in enumerate(differences):
        errors[f"fd_{i}"] = relative(v["delta_alpha_reduced"], -difference["derivative"])
        checks[f"fd_{i}"] = errors[f"fd_{i}"] <= 1e-6
    for name, mass, charge, energy in (
        ("positive", 2e-27, 1.602176634e-19, 1e4 * 1.602176634e-19),
        ("negative", 2e-27, -1.602176634e-19, 1e4 * 1.602176634e-19),
        ("double_energy", 2e-27, 1.602176634e-19, 2e4 * 1.602176634e-19),
        ("double_mass", 4e-27, 1.602176634e-19, 1e4 * 1.602176634e-19),
    ):
        saved = cell["absolute"][name]
        speed = math.sqrt(2 * energy / mass)
        time = v["transit_length"] / speed
        delta = math.sqrt(2 * mass * energy) * v["delta_alpha_reduced"] / charge
        expected = dict(
            speed_m_per_s=speed,
            action_kg_m2_per_s=math.sqrt(2 * mass * energy) * v["action"],
            time_s=time,
            delta_alpha_rad=delta,
            omega_alpha_rad_per_s=delta / time,
        )
        checks[f"particle_{name}"] = saved["particle"] == dict(
            mass=mass, charge=charge, energy_j=energy
        )
        for key, value in expected.items():
            checks[f"si_{name}_{key}"] = relative(saved[key], value) <= 1e-12
    return dict(checks=checks, errors=errors, all_pass=all(checks.values()))
