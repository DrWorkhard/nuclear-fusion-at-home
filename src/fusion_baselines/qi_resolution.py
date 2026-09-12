"""Pure controls and input-identity checks for the registered QI matrix."""

import copy

import numpy as np

MATRIX = ((201, 1), (401, 1), (201, 2), (401, 2))
NUMERICAL = frozenset(("ns_array", "ftol_array", "niter_array", "ntheta", "nzeta",
                       "iteration_style"))


def effective_input(original, ns, angular):
    if (ns, angular) not in MATRIX:
        raise ValueError("registered radial/angular cell required")
    result = copy.deepcopy(original)
    radial = [12, 25, 51, 101, 201] + ([401] if ns == 401 else [])
    tolerances = [1e-8, 1e-10, 1e-11, 1e-12, 1e-12] + ([1e-12] if ns == 401 else [])
    result.update(ns_array=radial, ftol_array=tolerances, niter_array=[10000] * len(radial),
                  ntheta=angular * (2 * original["mpol"] + 6),
                  nzeta=angular * (2 * original["ntor"] + 4), iteration_style="vmec_8_52")
    return result


def check_effective(original, effective, ns, angular):
    expected = effective_input(original, ns, angular)
    return effective == expected and all(effective[k] == v for k, v in original.items()
                                         if k not in NUMERICAL)


def mode_map(entries):
    result = {}
    for entry in entries:
        m, n, value = entry["m"], entry["n"], float(entry["value"])
        if int(m) != m or int(n) != n or not np.isfinite(value) or (m, n) in result:
            raise ValueError("unique finite integer Fourier modes required")
        result[m, n] = value
    return result


def author_input_checks(nml, converted):
    """Independent f90nml mapping vs the solver's parsed author-input JSON."""
    checks = {}
    for key, expected in nml.items():
        if key not in converted:
            raise ValueError(f"author input silently dropped: {key}")
        if key in ("rbc", "zbs", "rbs", "zbc"):
            n0, m0 = nml.start_index[key]
            source = {(m0 + mi, n0 + ni): float(value or 0)
                      for mi, row in enumerate(expected)
                      for ni, value in enumerate(row)}
            actual = mode_map(converted[key])
            error = max(abs(source.get(k, 0) - actual.get(k, 0))
                        for k in source.keys() | actual.keys())
            checks[key] = error <= 1e-12 * max(1, max(abs(v) for v in source.values()))
        else:
            value = converted[key]
            # f90nml represents a single-entry namelist array as a scalar.
            if isinstance(value, list) and not isinstance(expected, list):
                expected = [expected]
            checks[key] = value == expected
    return {k: bool(v) for k, v in checks.items()}


def boundary_errors(ds, effective):
    nfp = int(np.asarray(ds["nfp"][...]).item())
    m, n = np.asarray(ds["xm"][:]), np.asarray(ds["xn"][:]) / nfp
    errors = {}
    for key, wkey in (("rbc", "rmnc"), ("zbs", "zmns")):
        intended = mode_map(effective[key])
        actual = {(int(mm), int(nn)): float(v) for mm, nn, v in
                  zip(m, n, ds[wkey][-1], strict=True)}
        errors[key] = max(abs(intended.get(k, 0) - actual.get(k, 0))
                          for k in intended.keys() | actual.keys()) / max(
                              1, max(abs(v) for v in intended.values()))
    return errors
