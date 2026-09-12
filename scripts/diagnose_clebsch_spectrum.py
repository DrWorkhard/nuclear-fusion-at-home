"""Fixed-mode projection diagnostic on all original neighboring half surfaces."""

import argparse
import json
from pathlib import Path

import netCDF4
import numpy as np
from audit_qi_clebsch import checked, reference
from diagnose_clebsch_interpolation import endpoints

from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.resource_guard import GIB, space_check
from fusion_baselines.spectral_projection import mode_mask, project


def relative_rows(actual, expected):
    return np.max(abs(actual - expected), axis=(-2, -1)) / np.max(abs(expected), axis=(-2, -1))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new immutable spectral paths required")
    root = Path(__file__).resolve().parents[1]
    source = root / "evidence/qi-clebsch-interpolation-v1.json"
    audit = root / "evidence/qi-clebsch-interpolation-v1-audit.json"
    old, audited = json.loads(source.read_text()), json.loads(audit.read_text())
    if (
        old["status"] != "completed"
        or not audited["all_pass"]
        or audited["source"] != reference(source)
    ):
        raise ValueError("completed audited decomposition required")
    original = json.loads(checked(old["source"]).read_text())
    groups = {}
    for row, old_row in zip(old["grids"], original["grids"], strict=True):
        groups.setdefault((row["case"], row["surface"]), []).append((row, old_row))
    args.raw.mkdir(parents=True)
    report = dict(
        repository=git_state(root),
        status="running",
        all_pass=False,
        grids=[],
        source=reference(source),
        source_audit=reference(audit),
        protocol=reference(root / "docs/qi/QI_CLEBSCH_SPECTRAL_PROTOCOL.md"),
        code=[
            reference(root / p)
            for p in (
                "scripts/diagnose_clebsch_spectrum.py",
                "src/fusion_baselines/spectral_projection.py",
                "scripts/diagnose_clebsch_interpolation.py",
            )
        ],
        source_reclassified=False,
        absolute_drift_certified=False,
    )
    try:
        for (case, surface), prior in groups.items():
            wout_ref = prior[0][1]["wout"]
            with netCDF4.Dataset(checked(wout_ref)) as dataset:
                nfp = int(dataset["nfp"][...])
                m, n = np.asarray(dataset["xm_nyq"][:]), np.asarray(dataset["xn_nyq"][:])
                psi = -float(dataset["phi"][-1]) / (2 * np.pi)
            coarse = {}
            for size in (64, 128):
                space_check(root, 2 * GIB)
                if size <= 4 * max(float(np.max(abs(m))), float(np.max(abs(n / nfp)))):
                    raise ValueError("product spectrum is not resolved")
                phi, theta = np.meshgrid(
                    2 * np.pi * np.arange(size) / (size * nfp),
                    2 * np.pi * np.arange(size) / size,
                    indexing="ij",
                )
                fields, metadata = endpoints(checked(wout_ref), surface, theta, phi)
                mask = mode_mask(size, m, n, nfp)
                nested = []
                for old_row, _ in prior:
                    stride = size // old_row["resolution"]
                    with np.load(checked(old_row["arrays"]), allow_pickle=False) as saved:
                        nested.extend(
                            float(np.max(abs(value[:, ::stride, ::stride] - saved[key])))
                            / max(1, float(np.max(abs(saved[key]))))
                            for key, value in fields.items()
                        )
                arrays = dict(**fields, m=m, n=n, nfp=np.array(nfp), psi=np.array(psi), mask=mask)
                components = {}
                for component, bkey in (("poloidal", "bt"), ("toroidal", "bp")):
                    h = fields["iota"] - fields["lp"] if bkey == "bt" else 1 + fields["lt"]
                    with np.errstate(divide="raise", invalid="raise"):
                        rational = psi * h / fields["g"]
                    projected, coefficients, _ = project(rational, mask)
                    residual = fields["g"] * fields[bkey] - psi * h
                    _, residual_coefficients, stats = project(residual, mask)
                    error = relative_rows(projected, fields[bkey])
                    component_checks = dict(
                        projection=bool(np.max(error) <= 1e-5),
                        parseval=bool(np.max(stats["parseval_error"]) <= 1e-12),
                    )
                    values = dict(
                        projection_error=error.tolist(),
                        rational_error=relative_rows(rational, fields[bkey]).tolist(),
                        residual_spectrum={k: v.tolist() for k, v in stats.items()},
                    )
                    if size == 64:
                        coarse[component] = (projected.copy(), fields[bkey].copy())
                    else:
                        # Denominator remains the original component, not the difference signal.
                        refinement = np.max(
                            abs(projected[:, ::2, ::2] - coarse[component][0]), axis=(-2, -1)
                        ) / np.max(abs(coarse[component][1]), axis=(-2, -1))
                        values["refinement_error"] = refinement.tolist()
                        component_checks["refinement"] = bool(np.max(refinement) <= 1e-5)
                    components[component] = dict(**values, checks=component_checks)
                    for key, value in dict(
                        rational=rational,
                        projected=projected,
                        coefficients=coefficients,
                        residual=residual,
                        residual_coefficients=residual_coefficients,
                    ).items():
                        arrays[f"{component}_{key}"] = value
                path = args.raw / f"{case}-s{surface}-n{size}.npz"
                with path.open("xb") as stream:
                    np.savez_compressed(stream, **arrays)
                passed = max(nested) <= 1e-12 and all(
                    all(c["checks"].values()) for c in components.values()
                )
                row = dict(
                    case=case,
                    surface=surface,
                    resolution=size,
                    metadata=metadata,
                    wout=wout_ref,
                    arrays=reference(path),
                    nested_replay_error=max(nested),
                    components=components,
                    all_pass=passed,
                )
                report["grids"].append(row)
                write_json_atomic(args.output, report)
                print(case, surface, size, passed, components, flush=True)
        report.update(
            status="completed",
            all_pass=all(r["all_pass"] for r in report["grids"]),
            endpoint_grids_evaluated=2 * len(report["grids"]),
        )
    except Exception as error:
        report.update(status="error", all_pass=False, error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json_atomic(args.output, report)
    return 0 if report["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
