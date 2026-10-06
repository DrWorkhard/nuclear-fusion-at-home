"""Reference401 Wout consistency checks shared by portable intake and tracing.

Boundary/flux agreement does not establish identity of the unsampled interior.
"""

import numpy as np


def validate_reference(data, target_input):
    def read(key):
        value = np.ma.asarray(data[key][...], dtype=float).filled(np.nan)
        if not np.isfinite(value).all():
            raise ValueError(f"nonfinite Wout value: {key}")
        return value

    if read("nfp").item() != 2 or read("lasym__logical__").item() != 0:
        raise ValueError("symmetric nfp2 Wout required")
    if read("ns").item() != 401 or abs(read("phi")[-1] - target_input["phiedge"]) > 1e-14:
        raise ValueError("401-surface Wout with the input's edge flux required")
    m, n = read("xm"), read("xn") / 2
    if m.shape != n.shape or not (np.equal(m, np.round(m)).all()
                                and np.equal(n, np.round(n)).all()):
        raise ValueError("integer reference Fourier modes required")
    modes = list(zip(m.astype(int), n.astype(int), strict=True))
    if len(set(modes)) != len(modes):
        raise ValueError("unique reference Fourier modes required")
    for key, wkey in (("rbc", "rmnc"), ("zbs", "zmns")):
        intended = {(row["m"], row["n"]): row["value"] for row in target_input[key]}
        actual = dict(zip(modes, read(wkey)[-1], strict=True))
        error = max(abs(intended.get(k, 0) - actual.get(k, 0))
                    for k in intended.keys() | actual.keys())
        if error > 1e-12:
            raise ValueError(f"Wout boundary differs from input {key}: {error}")
