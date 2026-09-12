"""Fixed neighboring-half-grid residual decomposition, preserving all old failures."""

import argparse
import json
from pathlib import Path

import netCDF4
import numpy as np
from audit_qi_clebsch import checked, reference

from fusion_baselines.product_interpolation import decompose
from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.resource_guard import GIB, space_check


def endpoints(wout, surface, theta, phi):
    with netCDF4.Dataset(wout) as dataset:

        def read(key):
            value = np.ma.asarray(dataset[key][...], dtype=float).filled(np.nan)
            if not np.isfinite(value).all():
                raise ValueError(f"nonfinite Wout variable: {key}")
            return value

        ns = int(read("ns").item())
        full = np.linspace(0, 1, ns)
        half = (full[:-1] + full[1:]) / 2
        if not half[0] <= surface <= half[-1]:
            raise ValueError("interior half-grid interval required")
        upper = min(int(np.searchsorted(half, surface, side="right")), len(half) - 1)
        lower = upper - 1
        indices = np.array([lower, upper]) + 1
        weight = float((surface - half[lower]) / (half[upper] - half[lower]))
        m, n, mn, nn = [read(k) for k in ("xm", "xn", "xm_nyq", "xn_nyq")]
        angular = np.cos(m[:, None] * theta.ravel() - n[:, None] * phi.ravel())
        nyquist = np.cos(mn[:, None] * theta.ravel() - nn[:, None] * phi.ravel())

        def project(coeff, basis):
            return (coeff @ basis).reshape(2, *theta.shape)

        lam = read("lmns")[indices]
        fields = {
            out: project(read(key)[indices], nyquist)
            for out, key in (("g", "gmnc"), ("bt", "bsupumnc"), ("bp", "bsupvmnc"))
        }
        fields.update(
            lt=project(lam * m, angular),
            lp=project(-lam * n, angular),
            iota=np.broadcast_to(read("iotas")[indices, None, None], (2, *theta.shape)).copy(),
        )
    return fields, dict(
        indices=indices.tolist(), surfaces=half[[lower, upper]].tolist(), fraction=weight, ns=ns
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new immutable diagnostic paths required")
    root = Path(__file__).resolve().parents[1]
    source = root / "evidence/qi-clebsch-v1.json"
    audit = root / "evidence/qi-clebsch-v1-audit.json"
    old, audited = json.loads(source.read_text()), json.loads(audit.read_text())
    if (
        old["status"] != "completed"
        or not audited["all_pass"]
        or audited["source"] != reference(source)
    ):
        raise ValueError("completed fully audited original screen required")
    args.raw.mkdir(parents=True)
    report = dict(
        repository=git_state(root),
        status="running",
        all_pass=False,
        source=reference(source),
        source_audit=reference(audit),
        grids=[],
        protocol=reference(root / "docs/qi/QI_CLEBSCH_INTERPOLATION_PROTOCOL.md"),
        code=[
            reference(root / p)
            for p in (
                "scripts/diagnose_clebsch_interpolation.py",
                "src/fusion_baselines/product_interpolation.py",
            )
        ],
        original_screen_reclassified=False,
        absolute_drift_certified=False,
    )
    try:
        for number, row in enumerate(old["grids"]):
            space_check(root, 2 * GIB)
            with np.load(checked(row["arrays"]), allow_pickle=False) as original:
                fields, metadata = endpoints(
                    checked(row["wout"]), row["surface"], original["theta"], original["phi"]
                )
                t, psi = metadata["fraction"], original["psi"].item()
                replay = {
                    key: float(
                        np.max(abs((1 - t) * value[0] + t * value[1] - original[key]))
                        / max(1, float(np.max(abs(original[key]))))
                    )
                    for key, value in fields.items()
                }
                arrays, components = dict(**fields, fraction=np.array(t), psi=np.array(psi)), {}
                for component, bkey, hkey in (("poloidal", "bt", "lp"), ("toroidal", "bp", "lt")):
                    h = fields["iota"] - fields["lp"] if hkey == "lp" else 1 + fields["lt"]
                    old_h = (
                        original["iota"] - original["lp"] if hkey == "lp" else 1 + original["lt"]
                    )
                    norm = max(abs(psi) if hkey == "lp" else 0, float(np.max(abs(psi * old_h))))
                    nodes, average, correction, prediction = decompose(
                        fields["g"], fields[bkey], h, t, psi
                    )
                    residual = original["g"] * original[bkey] - psi * old_h
                    error = float(np.max(abs(prediction - residual)) / norm)
                    node_errors = [
                        float(
                            np.max(abs(v))
                            / max(abs(psi) if hkey == "lp" else 0, float(np.max(abs(psi * hn))))
                        )
                        for v, hn in zip(nodes, h, strict=True)
                    ]
                    components[component] = dict(
                        replay_error=error,
                        old_residual_norm=float(np.max(abs(residual)) / norm),
                        node_errors=node_errors,
                        node_screen_pass=all(v <= 1e-3 for v in node_errors),
                        average_node_norm=float(np.max(abs(average)) / norm),
                        product_correction_norm=float(np.max(abs(correction)) / norm),
                    )
                    for key, value in dict(
                        nodes=nodes,
                        average=average,
                        correction=correction,
                        prediction=prediction,
                        original=residual,
                    ).items():
                        arrays[f"{component}_{key}"] = value
            path = args.raw / f"grid-{number}.npz"
            with path.open("xb") as stream:
                np.savez_compressed(stream, **arrays)
            passed = max(replay.values()) <= 1e-12 and all(
                c["replay_error"] <= 1e-12 for c in components.values()
            )
            report["grids"].append(
                dict(
                    case=row["case"],
                    surface=row["surface"],
                    resolution=row["resolution"],
                    original_arrays=row["arrays"],
                    metadata=metadata,
                    replay_errors=replay,
                    components=components,
                    arrays=reference(path),
                    all_pass=passed,
                )
            )
            write_json_atomic(args.output, report)
            print(row["case"], row["surface"], row["resolution"], passed, components, flush=True)
        report.update(status="completed", all_pass=all(r["all_pass"] for r in report["grids"]))
    except Exception as error:
        report.update(status="error", all_pass=False, error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json_atomic(args.output, report)
    return 0 if report["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
