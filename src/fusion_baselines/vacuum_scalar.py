"""Independent scalar geometry and adaptive action derivatives in exact vacuum."""

import math
import warnings

from scipy.integrate import quad
from scipy.optimize import brentq


def scalar_vacuum(psi, bstar, alpha, *, record=None):
    result = {} if record is None else record
    result.update(psi=psi, bstar=bstar, alpha=alpha, status="running", integrals={}, warnings=[])
    calls = dict(
        root=0,
        roots_requested=0,
        roots_completed=0,
        action=0,
        transit_length=0,
        action_psi=0,
        action_alpha=0,
    )
    result["calls"] = calls
    if not all(math.isfinite(v) for v in (psi, bstar, alpha)) or psi <= 0 or bstar <= 1:
        raise ValueError("finite positive flux/trapped pitch required")

    def geometry(z):
        s = 1 + z
        x = math.sqrt(2 * psi) * math.cos(alpha) / s**0.7
        y = math.sqrt(2 * psi) * math.sin(alpha) / s**0.3
        xp, yp = -0.7 * x / s, -0.3 * y / s
        magnitude = math.sqrt(0.49 * x * x + 0.09 * y * y + s * s)
        length = math.sqrt(1 + xp * xp + yp * yp)
        bpsi = (0.49 * x * x + 0.09 * y * y) / (2 * psi * magnitude)
        xalpha = -math.sqrt(2 * psi) * math.sin(alpha) / s**0.7
        yalpha = math.sqrt(2 * psi) * math.cos(alpha) / s**0.3
        balpha = (0.49 * x * xalpha + 0.09 * y * yalpha) / magnitude
        return magnitude, length, bpsi, balpha

    def equation(z):
        calls["root"] += 1
        return geometry(z)[0] - bstar

    try:
        roots = []
        for lower, upper in ((1e-6 - 1, 0.0), (0.0, bstar - 1)):
            if equation(lower) * equation(upper) >= 0:
                raise ValueError("fixed scalar vacuum bracket failed")
            calls["roots_requested"] += 1
            roots.append(brentq(equation, lower, upper, xtol=5e-15, rtol=4 * math.ulp(1.0)))
            calls["roots_completed"] += 1
            result["roots"] = roots.copy()
        midpoint, halfspan = sum(roots) / 2, (roots[1] - roots[0]) / 2
        for name in ("action", "transit_length", "action_psi", "action_alpha"):

            def integrand(u, name=name):
                calls[name] += 1
                z = midpoint + halfspan * math.sin(u)
                magnitude, length, bpsi, balpha = geometry(z)
                q = 1 - magnitude / bstar
                if q <= 0:
                    raise ValueError("scalar node outside open vacuum bounce interval")
                rootq, jac = math.sqrt(q), halfspan * math.cos(u)
                if name == "action":
                    return rootq * length * jac
                if name == "transit_length":
                    return length * jac / rootq
                derivative = bpsi if name == "action_psi" else balpha
                return derivative * (rootq / (1 + z) - length / (2 * bstar * rootq)) * jac

            messages = []
            result["active_integral"] = name
            try:
                with warnings.catch_warnings(record=True) as messages:
                    warnings.simplefilter("always")
                    value, estimate = quad(
                        integrand, -math.pi / 2, math.pi / 2, epsabs=1e-10, epsrel=1e-10, limit=200
                    )
                result["integrals"][name] = dict(value=value, absolute_error_estimate=estimate)
            finally:
                result["warnings"].extend(
                    dict(integral=name, message=str(w.message)) for w in messages
                )
        result.update(status="completed", active_integral=None)
    except Exception as error:
        result.update(status="error", error=f"{type(error).__name__}: {error}")
        raise
    return result
