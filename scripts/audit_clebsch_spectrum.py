"""Independent trigonometric projection and band-energy audit of cached QI fields."""

import argparse
import json
from pathlib import Path

import numpy as np

from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.spectral_projection import explicit_projection


def reference(path):
    return dict(path=str(path.resolve()), sha256=sha256_file(path))


def checked(ref):
    path = Path(ref["path"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError(f"spectral reference changed: {path}")
    return path


def direct_coefficients(values, mask):
    size = mask.shape[0]
    angles = 2 * np.pi * np.arange(size) / size
    result = np.zeros(values.shape, dtype=complex)
    for i, j in np.argwhere(mask):
        ki, kj = (i if i <= size // 2 else i - size), (j if j <= size // 2 else j - size)
        phase = ki * angles[:, None] + kj * angles[None, :]
        result[..., i, j] = np.mean(values * np.cos(phase), axis=(-2, -1)) - 1j * np.mean(
            values * np.sin(phase), axis=(-2, -1)
        )
    return result


def close(actual, expected, scale=1):
    return bool(
        np.shape(actual) == np.shape(expected)
        and np.isfinite(actual).all()
        and np.max(abs(np.asarray(actual) - expected)) / scale <= 1e-12
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable spectral audit required")
    root = Path(__file__).resolve().parents[1]
    report = json.loads(args.source.read_text())
    for ref in [report["protocol"], *report["code"]]:
        checked(ref)
    expected = [
        (case, s, n)
        for case in ("nfp2-vacuum", "nfp2-beta2", "nfp3-vacuum", "nfp3-beta2")
        for s in (0.25, 0.5, 0.75)
        for n in (64, 128)
    ]
    if (
        report["status"] != "completed"
        or [(r["case"], r["surface"], r["resolution"]) for r in report["grids"]] != expected
    ):
        raise ValueError("all fixed spectral grids required")
    rows, coarse, calls = [], {}, 0
    for row in report["grids"]:
        checked(row["wout"])
        checks, screens = {}, {}
        with np.load(checked(row["arrays"]), allow_pickle=False) as data:
            size, mask, psi = row["resolution"], data["mask"], data["psi"].item()
            expected_pairs = set()
            for m, n in zip(data["m"], data["n"] / data["nfp"], strict=True):
                expected_pairs.update(
                    {(-int(n) % size, int(m) % size), (int(n) % size, -int(m) % size)}
                )
            checks["mode_mask"] = set(map(tuple, np.argwhere(mask))) == expected_pairs
            for component, bkey in (("poloidal", "bt"), ("toroidal", "bp")):
                record = row["components"][component]
                h = data["iota"] - data["lp"] if bkey == "bt" else 1 + data["lt"]
                rational, residual = psi * h / data["g"], data["g"] * data[bkey] - psi * h
                c = direct_coefficients(rational, mask)
                cr = direct_coefficients(residual, mask)
                calls += 2
                projected = explicit_projection(c, mask)
                denominator = np.max(abs(data[bkey]), axis=(-2, -1))
                error = np.max(abs(projected - data[bkey]), axis=(-2, -1)) / denominator
                total = np.mean(residual**2, axis=(-2, -1))
                inside = np.sum(abs(cr) ** 2, axis=(-2, -1))
                stats = record["residual_spectrum"]
                checks[component] = bool(
                    close(rational, data[f"{component}_rational"], max(1, np.max(abs(rational))))
                    and close(residual, data[f"{component}_residual"])
                    and close(c, data[f"{component}_coefficients"] * mask, max(1, np.max(abs(c))))
                    and close(
                        projected, data[f"{component}_projected"], max(1, np.max(abs(projected)))
                    )
                    and close(error, record["projection_error"])
                    and close(total, stats["energy"], max(float(np.max(total)), 1e-300))
                    and close(inside, stats["inside"], max(float(np.max(total)), 1e-300))
                    and close(total - inside, stats["outside"], max(float(np.max(total)), 1e-300))
                )
                passed = bool(np.max(error) <= 1e-5)
                checks[f"{component}_classification"] = passed == record["checks"]["projection"]
                key = (row["case"], row["surface"], component)
                if size == 64:
                    coarse[key] = projected.copy(), denominator.copy()
                else:
                    refinement = (
                        np.max(abs(projected[:, ::2, ::2] - coarse[key][0]), axis=(-2, -1))
                        / coarse[key][1]
                    )
                    refined = bool(np.max(refinement) <= 1e-5)
                    checks[f"{component}_refinement"] = close(
                        refinement, record["refinement_error"]
                    ) and (refined == record["checks"]["refinement"])
                    passed &= refined
                screens[component] = passed
        rows.append(
            dict(
                case=row["case"],
                surface=row["surface"],
                resolution=size,
                checks=checks,
                all_pass=all(checks.values()),
                physical_screens=screens,
            )
        )
    result = dict(
        repository=git_state(root),
        source=reference(args.source),
        grids=rows,
        all_pass=all(r["all_pass"] for r in rows),
        spectral_hypothesis_screen_pass=all(all(r["physical_screens"].values()) for r in rows),
        new_field_evaluations=0,
        direct_masked_DFT_calls=calls,
        explicit_projection_calls=2 * len(rows),
        absolute_drift_certified=False,
        code=[
            reference(Path(__file__)),
            reference(root / "src/fusion_baselines/spectral_projection.py"),
        ],
    )
    write_json_atomic(args.output, result)
    print(json.dumps({k: result[k] for k in ("all_pass", "spectral_hypothesis_screen_pass")}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
