"""Freeze a coil target specification for a new plasma (#115).

Binds the input JSON hash, the Wout hash and its vmecpp version, B2 computed once
from the Wout's 64x64 archives, the signed flux (-phiedge) and a paired seed snapshot
with its current. Writes `spec.json` and `seed.json` to a fresh directory. The tools
then take `--target-spec spec.json --wout <the same Wout>`.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))

from fusion_baselines import coil_check as check  # noqa: E402
from fusion_baselines import wout_target  # noqa: E402
from fusion_baselines.clear_coil_field_audit import archived_target  # noqa: E402
from fusion_public.data import load as load_candidate  # noqa: E402


def stored(path):
    path = Path(path).resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def run(label, source, sha256, wout, vmecpp, output, snapshot=None, candidate=None):
    check.need((snapshot is None) != (candidate is None), "exactly one seed snapshot or candidate")
    check.need(check.LABEL.fullmatch(label) and label not in check.REGISTERED,
               "distinct lowercase target label required (not a registered target)")
    data = check.read_json(check.bind(source, sha256, {}))
    archives, wout_sha256 = wout_target.archives(wout, data)
    measured = {n: archived_target(archives, n)["B2_scale"] for n in (32, 64)}
    check.need(abs(measured[32]/measured[64] - 1) <= 1e-9, "grid-independent B2 required")
    entry = dict(input=str(Path(source).resolve()), input_sha256=sha256,
                 wout_sha256=wout_sha256, B2=float(measured[64]), flux=-float(data["phiedge"]))
    check.TARGETS[label] = entry  # Provisional, only to normalize the seed below.
    if snapshot is not None:
        seed = check.retarget_snapshot(check.read_json(snapshot), data, label)
        origin = dict(snapshot=stored(snapshot), sha256=check.digest(snapshot))
    else:
        seed = check.candidate_snapshot(load_candidate(candidate), data, target_id=label)
        origin = dict(candidate=stored(candidate), sha256=check.digest(candidate))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output/"seed.json").write_text(json.dumps(seed, sort_keys=True, indent=2) + "\n")
    spec = dict(schema=check.SPEC_SCHEMA, target_id=label,
                input=dict(path=stored(source), sha256=sha256),
                wout=dict(sha256=wout_sha256, vmecpp=vmecpp),
                B2=entry["B2"], B2_measured_32=float(measured[32]), flux=entry["flux"],
                seed=dict(snapshot_sha256=check.digest(output/"seed.json"),
                          current_A=1e5*seed["scale"], origin=origin),
                note="errors against different targets are not directly comparable")
    (output/"spec.json").write_text(json.dumps(spec, indent=2) + "\n")
    del check.TARGETS[label]
    check.need(check.load_target_spec(output/"spec.json") == label, "spec round trip")
    return spec


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-id", required=True)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--input-sha256", required=True)
    parser.add_argument("--wout", required=True, type=Path)
    parser.add_argument("--vmecpp", required=True, help="vmecpp version that produced the Wout")
    parser.add_argument("--output", required=True, type=Path, help="fresh directory")
    seed = parser.add_mutually_exclusive_group(required=True)
    seed.add_argument("--seed-snapshot", type=Path, help="native snapshot of another target")
    seed.add_argument("--seed-candidate", type=Path, help="public six-coil candidate JSON")
    args = parser.parse_args()
    print(json.dumps(run(args.target_id, args.input.resolve(), args.input_sha256,
                         args.wout.resolve(), args.vmecpp, args.output.resolve(),
                         args.seed_snapshot, args.seed_candidate), indent=2))
