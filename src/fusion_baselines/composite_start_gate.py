"""Fixed-start replay and explicit composite gate; no substituted numerical values."""

import hashlib

import numpy as np


def reference_checks(x, values, jacobian, qualified):
    checks = {}
    for name, actual, expected, shape in (
        ("x", x, qualified["x"], (207,)),
        ("values", values, qualified["values"], (138,)),
        ("jacobian", jacobian, qualified["jacobian"], (138, 207)),
    ):
        actual, expected = np.asarray(actual), np.asarray(expected)
        if (actual.shape != shape or expected.shape != shape
                or not np.isfinite(actual).all() or not np.isfinite(expected).all()):
            raise ValueError("complete finite native and qualified arrays required")
        error = float(np.max(abs(actual-expected) / np.maximum(1, abs(expected))))
        checks[name + "_error"] = error
        checks[name + "_pass"] = bool(np.array_equal(actual, expected) if name == "x"
                                     else error <= 1e-12)
    return checks


def startup_replay(x, direction, permutation, ledger, original):
    p = np.asarray(permutation)
    if (p.shape != (207,) or not np.issubdtype(p.dtype, np.integer)
            or sorted(p.tolist()) != list(range(207)) or len(ledger) != 9
            or len(original["evaluations"]) != 9):
        raise ValueError("full physical permutation and both nine-bundle ledgers required")
    inverse = np.argsort(p)
    vectors = [x]
    for h in (1e-5, 1e-6, 1e-7, 1e-8):
        vectors.extend((x+h*direction, x-h*direction))
    rows = []
    for vector, current, old in zip(vectors, ledger, original["evaluations"], strict=True):
        actual, expected = np.asarray(current["values"]), np.asarray(old["values"])
        if actual.shape != (138,) or expected.shape != (138,):
            raise ValueError("all138 startup values required")
        error = float(np.max(abs(actual-expected) / np.maximum(1, abs(expected))))
        rows.append(dict(target_hash=hashlib.sha256(vector.tobytes()).hexdigest()
                          == current["x_sha256"],
                         source_hash=hashlib.sha256(vector[inverse].tobytes()).hexdigest()
                          == old["x_sha256"], value_error=error,
                         values_pass=bool(np.isfinite(error) and error <= 1e-12)))
    return rows


def composite_gate(fd_errors, reference, replay):
    error = np.asarray(fd_errors)
    if error.shape != (138,) or not np.isfinite(error).all() or np.any(error < 0):
        raise ValueError("all138 finite nonnegative FD errors required")
    nonpair = float(np.r_[error[:6], error[126:]].max())
    gate = (all(reference[k+"_pass"] for k in ("x", "values", "jacobian"))
            and len(replay) == 9 and all(r["target_hash"] and r["source_hash"] and r["values_pass"]
                                         for r in replay) and nonpair <= 1e-6)
    return dict(original_all_row_fd_pass=bool(error.max() <= 1e-6),
                original_all_row_fd_maximum=float(error.max()), nonpair_fd_maximum=nonpair,
                gradient_screen_pass=bool(gate))
