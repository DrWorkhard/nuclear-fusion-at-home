"""Independent arithmetic replay; does not import the measurement/screen helpers."""

import numpy as np


def audit_family(family, original):
    a0 = family["finest_anchor_action"]
    checks = dict(
        anchor_identity=a0 == original["finest_anchor_action"],
        old_stencil=np.array_equal(
            family["gauges"]["0"]["action_stencil"], original["action_stencil"]
        ),
        radial_arithmetic=True,
        chain_arithmetic=True,
    )
    if not np.isfinite(a0) or a0 <= 0:
        return {**checks, "anchor_identity": False}
    slopes, recomputed = (-1, 0, 1), {}
    for slope in slopes:
        g = family["gauges"][str(slope)]
        actions = np.asarray(g["action_stencil"])
        if actions.shape != (3, 3, 2) or not np.isfinite(actions).all() or (actions <= 0).any():
            checks["radial_arithmetic"] = False
            continue
        d = (actions[:, :, 1] - actions[:, :, 0]) / (2 * np.array([0.04, 0.02, 0.01])[None, :])
        normalized = d / a0
        estimate = float(normalized[-1, -1])
        trace = float(abs(normalized[-1, -1] - normalized[-2, -1]))
        radial = float(abs(normalized[-1, -1] - normalized[-1, -2]))
        allowance = 4 * (trace + radial)
        tolerance = max(0.01, 0.05 * abs(estimate))
        refined = trace <= tolerance and radial <= tolerance
        sign = "unresolved"
        if refined and estimate + allowance < 0:
            sign = "negative"
        elif refined and estimate - allowance > 0:
            sign = "positive"
        expected = dict(
            estimate=estimate,
            trace_change=trace,
            radial_change=radial,
            tolerance=tolerance,
            empirical_allowance=allowance,
            refinement_pass=refined,
            sign=sign,
        )
        checks["radial_arithmetic"] &= bool(
            np.array_equal(d, g["derivatives"])
            and np.array_equal(normalized, g["normalized_derivatives"])
            and all(g[k] == v for k, v in expected.items())
        )
        recomputed[slope] = (d[-1, -1], sign)
    aa = np.asarray(family["alpha_action_stencil"])
    if aa.shape != (2, 2) or not np.isfinite(aa).all() or (aa <= 0).any() or len(recomputed) != 3:
        return {**checks, "chain_arithmetic": False}
    dalpha = (aa[:, 1] - aa[:, 0]) / (2 * np.array([0.01, 0.005]))
    for slope in (-1, 1):
        chain = family["chain"][str(slope)]
        predicted = recomputed[0][0] + slope * dalpha[-1]
        error = abs(recomputed[slope][0] - predicted) / a0
        limit = max(0.01, 0.05 * abs(recomputed[slope][0] / a0))
        change = abs(dalpha[-1] - dalpha[0]) / a0
        alpha_limit = max(0.01, 0.05 * abs(dalpha[-1] / a0))
        expected = dict(
            predicted_derivative=predicted,
            normalized_chain_error=error,
            chain_allowance=limit,
            alpha_change=change,
            alpha_allowance=alpha_limit,
            chain_pass=error <= limit,
            alpha_refinement_pass=change <= alpha_limit,
        )
        checks["chain_arithmetic"] &= bool(
            np.array_equal(dalpha, chain["alpha_derivatives"])
            and all(chain[k] == v for k, v in expected.items())
        )
    checks["old_sign_identity"] = family["old_zero_sign_equal"] == (
        recomputed[0][1] == original["sign"]
    )
    checks["old_stencil_flag"] = family["old_zero_stencil_exact"] == checks["old_stencil"]
    checks["sign_change_flag"] = family["gauge_signs_equal"] == (
        len({v[1] for v in recomputed.values()}) == 1
    )
    return {k: bool(v) for k, v in checks.items()}


def audit_cell_binding(cell, original, nfp):
    """Independently verify all interval edges and reconstruct every stored stencil."""
    anchors = np.asarray([f["anchor"]["phi_interval"] for f in original["families"]])
    window = np.array([1, 3]) * 2 * np.pi / nfp
    radial, alpha = {}, {}
    checks = dict(
        all_rows=bool(cell["matching_pass"] and len(cell["wells"]) == 67),
        matching_edges=True,
        stencils_bound=True,
        anchors_bound=len(cell["families"]) == len(original["families"]),
    )
    for row in cell["wells"]:
        complete = [w for w in row["wells"] if w["complete"]]
        candidate = np.asarray([w["phi_interval"] for w in complete])
        if not complete or candidate.shape != (len(complete), 2) or "matches" not in row:
            checks["matching_edges"] = False
            continue
        overlap = np.minimum(anchors[:, None, 1], candidate[None, :, 1]) - np.maximum(
            anchors[:, None, 0], candidate[None, :, 0]
        )
        short = np.minimum(np.diff(anchors, axis=1), np.diff(candidate, axis=1).T)
        distance = np.max(np.abs(anchors[:, None, :] - candidate[None, :, :]), axis=2)
        edges = (overlap > 0.5 * short) & (distance < 0.25 * np.diff(anchors, axis=1))
        central = set(
            np.flatnonzero(
                (candidate.mean(axis=1) >= window[0]) & (candidate.mean(axis=1) <= window[1])
            )
        )
        chosen = np.argmax(edges, axis=1)
        valid = (
            np.all(edges.sum(axis=1) == 1)
            and np.all(edges.sum(axis=0) <= 1)
            and central <= set(chosen)
            and np.array_equal(chosen, row["matches"])
        )
        checks["matching_edges"] &= bool(valid)
        if not valid:
            continue
        actions = [complete[i]["action"] for i in chosen]
        if row["kind"] == "radial":
            key = row["slope"], row["level"], row["s"]
            checks["all_rows"] &= key not in radial
            radial[key] = actions
        else:
            key = row["alpha_offset"]
            checks["all_rows"] &= key not in alpha
            alpha[key] = actions
    for i, f in enumerate(cell["families"]):
        checks["anchors_bound"] &= f["anchor"] == original["families"][i]["anchor"]
        try:
            for c in (-1, 0, 1):
                stencil = [
                    [
                        [
                            radial[c, level, round(0.5 - h, 2)][i],
                            radial[c, level, round(0.5 + h, 2)][i],
                        ]
                        for h in (0.04, 0.02, 0.01)
                    ]
                    for level in range(3)
                ]
                checks["stencils_bound"] &= np.array_equal(
                    stencil, f["gauges"][str(c)]["action_stencil"]
                )
            checks["stencils_bound"] &= np.array_equal(
                [[alpha[-h][i], alpha[h][i]] for h in (0.01, 0.005)], f["alpha_action_stencil"]
            )
            checks["anchors_bound"] &= f["finest_anchor_action"] == radial[0, 2, 0.5][i]
        except (KeyError, IndexError):
            checks["stencils_bound"] = False
    return {k: bool(v) for k, v in checks.items()}
