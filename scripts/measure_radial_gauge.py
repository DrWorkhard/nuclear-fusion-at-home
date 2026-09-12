"""Fixed four-case radial field-line-gauge diagnosis with exact old-trace replay."""

import argparse
import json
import time
from collections import Counter
from pathlib import Path

import numpy as np
from measure_radial_action import NPHI, RADII, STEPS, wells_on_line

from fusion_baselines.gauge_action import gauge_chain_rule
from fusion_baselines.provenance import git_state, host_state, sha256_file, write_json_atomic
from fusion_baselines.radial_action import match_intervals, radial_sign_screen
from fusion_baselines.vmec_trace import trace_geometry


def reference(path):
    return dict(path=str(path.resolve()), sha256=sha256_file(path))


def checked(ref):
    path = Path(ref["path"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError(f"input hash mismatch: {path}")
    return path


def run_case(source, destination, raw, provenance):
    old = json.loads(source.read_text())
    if old["status"] != "completed" or old["summary"]["matching_failed_cells"]:
        raise ValueError("completed fully matched historical radial case required")
    wout = checked(old["wout"])
    name, nfp = old["case"], int(old["case"][3])
    started = time.monotonic()
    report = dict(
        **provenance,
        source=reference(source),
        case=name,
        wout=reference(wout),
        status="running",
        traces=[],
        cells=[],
        global_maximum_J_certified=False,
    )
    traces, offsets = {}, {}
    raw.mkdir(parents=True)

    def save(trace, filename, **metadata):
        path = raw / filename
        with path.open("xb") as stream:
            np.savez_compressed(stream, **trace)
        ref = {**reference(path), **metadata}
        report["traces"].append(ref)
        return ref

    try:
        for ref in old["traces"]:
            level, s = ref["level"], ref["s"]
            trace = trace_geometry(wout, s, NPHI[level], 8, 4)
            with np.load(checked(ref), allow_pickle=False) as data:
                equal = set(data.files) == set(trace) and all(
                    np.array_equal(data[k], trace[k]) for k in trace
                )
            save(
                trace,
                f"c0-level{level}-s{s}.npz",
                kind="radial",
                slope=0,
                level=level,
                s=s,
                historical=ref,
                exact_replay=bool(equal),
            )
            if not equal:
                raise ValueError(
                    f"zero-gauge historical array replay differs at level={level}, s={s}"
                )
            traces[0, level, s] = trace
        for slope in (-1, 1):
            for level, nphi in enumerate(NPHI):
                for s in RADII:
                    if s == 0.5:
                        traces[slope, level, s] = traces[0, level, s]
                        continue
                    offset = slope * (s - 0.5)
                    trace = trace_geometry(wout, s, nphi, 8, 4, alpha_offset=offset)
                    traces[slope, level, s] = trace
                    save(
                        trace,
                        f"c{slope}-level{level}-s{s}.npz",
                        kind="radial",
                        slope=slope,
                        level=level,
                        s=s,
                        alpha_offset=offset,
                    )
        for h in (0.01, 0.005):
            for sign in (-1, 1):
                offset = sign * h
                trace = trace_geometry(wout, 0.5, 3201, 8, 4, alpha_offset=offset)
                offsets[offset] = trace
                save(trace, f"alpha{offset}.npz", kind="alpha", alpha_offset=offset, s=0.5, level=2)
        report["s0_shared_between_gauges"] = True
        report["new_trace_count"] = len(report["traces"])
        window = np.array([1, 3]) * 2 * np.pi / nfp
        write_json_atomic(destination, report)
        for old_cell in old["cells"]:
            alpha, bstar = old_cell["alpha_index"], old_cell["Bstar"]
            anchors = [family["anchor"] for family in old_cell["families"]]
            intervals = [w["phi_interval"] for w in anchors]
            cell = dict(
                alpha_index=alpha,
                Bstar=bstar,
                q=old_cell["q"],
                wells=[],
                families=[],
                matching_pass=False,
            )
            report["cells"].append(cell)
            mapped, alpha_mapped = {}, {}
            try:
                for (slope, level, s), trace in traces.items():
                    wells = wells_on_line(trace, alpha, bstar)
                    complete = [w for w in wells if w["complete"]]
                    row = dict(kind="radial", slope=slope, level=level, s=s, wells=wells)
                    cell["wells"].append(row)
                    indices = match_intervals(
                        intervals, [w["phi_interval"] for w in complete], window
                    )
                    row["matches"] = indices.tolist()
                    mapped[slope, level, s] = [complete[i]["action"] for i in indices]
                for offset, trace in offsets.items():
                    wells = wells_on_line(trace, alpha, bstar)
                    complete = [w for w in wells if w["complete"]]
                    row = dict(kind="alpha", alpha_offset=offset, wells=wells)
                    cell["wells"].append(row)
                    indices = match_intervals(
                        intervals, [w["phi_interval"] for w in complete], window
                    )
                    row["matches"] = indices.tolist()
                    alpha_mapped[offset] = [complete[i]["action"] for i in indices]
            except ValueError as error:
                cell["matching_error"] = str(error)
                continue
            cell["matching_pass"] = True
            for family_index, anchor in enumerate(anchors):
                a0 = mapped[0, 2, 0.5][family_index]
                gauges = {}
                for slope in (-1, 0, 1):
                    stencil = np.array(
                        [
                            [
                                [
                                    mapped[slope, level, round(0.5 - h, 2)][family_index],
                                    mapped[slope, level, round(0.5 + h, 2)][family_index],
                                ]
                                for h in STEPS
                            ]
                            for level in range(3)
                        ]
                    )
                    gauges[str(slope)] = dict(
                        action_stencil=stencil.tolist(), **radial_sign_screen(stencil, a0)
                    )
                alpha_actions = np.array(
                    [
                        [alpha_mapped[-h][family_index], alpha_mapped[h][family_index]]
                        for h in (0.01, 0.005)
                    ]
                )
                chain = {
                    str(slope): gauge_chain_rule(
                        gauges["0"]["derivatives"][-1][-1],
                        gauges[str(slope)]["derivatives"][-1][-1],
                        alpha_actions,
                        a0,
                        slope,
                    )
                    for slope in (-1, 1)
                }
                original = old_cell["families"][family_index]
                cell["families"].append(
                    dict(
                        anchor=anchor,
                        finest_anchor_action=a0,
                        gauges=gauges,
                        alpha_action_stencil=alpha_actions.tolist(),
                        chain=chain,
                        old_zero_stencil_exact=bool(
                            np.array_equal(
                                gauges["0"]["action_stencil"], original["action_stencil"]
                            )
                        ),
                        old_zero_sign_equal=gauges["0"]["sign"] == original["sign"],
                        gauge_signs_equal=len({v["sign"] for v in gauges.values()}) == 1,
                    )
                )
        families = [f for c in report["cells"] for f in c["families"]]
        report["checks"] = dict(
            all_old_traces_exact=all(
                r["exact_replay"] for r in report["traces"] if "historical" in r
            ),
            all_cells_matched=all(c["matching_pass"] for c in report["cells"]),
            all_old_stencils_exact=all(f["old_zero_stencil_exact"] for f in families),
            all_old_signs_equal=all(f["old_zero_sign_equal"] for f in families),
            all_chain_rules=all(c["chain_pass"] for f in families for c in f["chain"].values()),
            all_alpha_refinements=all(
                c["alpha_refinement_pass"] for f in families for c in f["chain"].values()
            ),
            all_radial_refinements=all(
                g["refinement_pass"] for f in families for g in f["gauges"].values()
            ),
        )
        report["summary"] = dict(
            matched_families=len(families),
            failed_cells=sum(not c["matching_pass"] for c in report["cells"]),
            changed_sign_families=sum(not f["gauge_signs_equal"] for f in families),
            sign_counts={
                str(c): dict(Counter(f["gauges"][str(c)]["sign"] for f in families))
                for c in (-1, 0, 1)
            },
        )
        report.update(status="completed", diagnostic_checks_pass=all(report["checks"].values()))
    except Exception as error:
        report.update(status="error", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        report["elapsed_seconds"] = time.monotonic() - started
        write_json_atomic(destination, report)
    print(
        json.dumps({"case": name, "checks": report["checks"], "summary": report["summary"]}),
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new immutable output directories required")
    root = Path(__file__).resolve().parents[1]
    provenance = dict(
        schema_version=1,
        repository=git_state(root),
        host=host_state(),
        protocol=reference(root / "docs/qi/QI_RADIAL_GAUGE_PROTOCOL.md"),
        code=[
            reference(root / p)
            for p in (
                "scripts/measure_radial_gauge.py",
                "scripts/measure_radial_action.py",
                "src/fusion_baselines/vmec_trace.py",
                "src/fusion_baselines/bounce_action.py",
                "src/fusion_baselines/radial_action.py",
                "src/fusion_baselines/gauge_action.py",
            )
        ],
    )
    args.output.mkdir(parents=True)
    args.raw.mkdir(parents=True)
    for nfp in (2, 3):
        for state in ("vacuum", "beta2"):
            name = f"nfp{nfp}-{state}"
            run_case(
                root / f"evidence/qi-radial-action-v1/{name}.json",
                args.output / f"{name}.json",
                args.raw / name,
                provenance,
            )


if __name__ == "__main__":
    main()
