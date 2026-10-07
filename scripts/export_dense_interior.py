"""Re-export exact published #25 targets; NumPy is needed only for NPZ extraction."""

import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from fusion_public.data import canonical, load_case, parameter_names, sha  # noqa: E402

ARCHIVE = "05a4511084912fea9bd8d03e81f01018882396b8"
MANIFEST = "3f8ddda02e28f018c466d396aa1c93cf81a6cf90f2e63a934b0d44aa67534d1b"
PRODUCER = "a551289e63e44d7dbae7b5d5a0e5f4b6026db257"
FROZEN_FLUX = -0.03141592653589793
TARGETS = {
    "reference401": ("evidence/plasma-design-v2/reference-input-401.json",
                     "57394ef682f3c6399faa03012abc02da2eb1ce40703a4f99640ece3d07e5691f",
                     "83dc45b911a1e8290c3e97c7e28d4de28fcff6021b93d55df2f91d6dd3751c5e",
                     1.6293829620247962),
    "selected401": ("evidence/plasma-balanced-v1/selected-input-401.json",
                    "6bec3483eaced499bafe7ee94b16aa960d219ec1fec86cc0690012f8ebdb033e",
                    "8cd6bebfc29963f80645acf25e1a3db194e4db381365b17a89b9844554f51b52",
                    1.6313464444829588),
}


def export(archive, output, controls):
    start = time.monotonic()
    assert shutil.disk_usage(output.parent).free >= 3 * 1024**3, "3 GiB reserve required"
    root = archive / "evidence/issue25-matched-v1"
    raw = (root / "manifest.json").read_bytes()
    assert sha(raw) == MANIFEST, "Published manifest changed"
    manifest = json.loads(raw)
    for name, expected in manifest.items():
        with (root / name).open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == expected, name
    output.mkdir(exist_ok=False)
    controls.mkdir(parents=True, exist_ok=False)
    case, _ = load_case()
    files = {}

    def write(directory, name, value):
        data = canonical(value) + b"\n"
        assert len(data) < 2 * 1024**2, "Portable JSON must fit existing reader"
        with (directory / name).open("xb") as stream:
            stream.write(data)
        return sha(data)

    for target, (input_name, input_hash, wout_hash, b2) in TARGETS.items():
        raw = (archive / input_name).read_bytes()
        assert sha(raw) == input_hash, "Original input changed"
        document = json.loads(raw)
        name = f"{target}/fit/interior/level-2.npz"
        snapshot_name = f"{target}/fit/selected-snapshot.json"
        snapshot = json.loads((root / snapshot_name).read_bytes())
        assert (snapshot["nbase"], snapshot["order"], snapshot["nfp"]) == (6, 5, 2)
        assert snapshot["B2_scale"] == b2 and snapshot["target_flux"] == FROZEN_FLUX
        factors = []
        for original, public in zip(snapshot["physical"], case["physical"], strict=True):
            for key in ("base_index", "period", "flip"):
                assert original[key] == public[key], "Physical copy order changed"
            assert np.max(np.abs(np.array(original["matrix"]) - public["matrix"])) < 1e-15
            factors.append(original["current"] / public["current"])
        assert max(factors) - min(factors) < 1e-15, "Signed current ratios differ"
        with np.load(root / name, allow_pickle=False) as arrays:
            points, fields = arrays["inner_points"], arrays["inner_target"]
            assert points.shape == fields.shape == (12288, 3)
            assert np.all(np.isfinite(points)) and np.all(np.isfinite(fields))
            assert abs(np.mean(np.sum(fields**2, axis=1)) / b2 - 1) < 1e-14
            rows = np.column_stack((points, fields)).tolist()
            # Round-trip every coordinate and target component, not just sparse controls.
            assert np.array_equal(np.array(json.loads(canonical(rows))),
                                  np.column_stack((points, fields)))
            packet = dict(
                schema_version=1, packet_id="clear-coil-interior-v1", target_id=target,
                coordinates="Cartesian xyz in metres; Cartesian B in tesla",
                grid=dict(s=[0.25, 0.5, 0.75], nphi=64, ntheta=64,
                          phi="pi*j/64", theta="2*pi*k/64 (VMEC theta)",
                          ordering="s, geometric phi, VMEC theta; theta fastest",
                          periodic_endpoints=False, realized_flux_labels=False),
                B2_scale_T2=b2, signed_target_flux_Wb=FROZEN_FLUX,
                boundary={key: document[key] for key in ("nfp", "rbc", "zbs", "phiedge")},
                provenance=dict(archive_commit=ARCHIVE, archive_manifest_sha256=MANIFEST,
                                producer_evaluator=PRODUCER, input_sha256=input_hash,
                                wout_sha256=wout_hash, source_npz=name,
                                source_npz_sha256=manifest[name]),
                samples_xyz_B=rows,
            )
            files[f"{target}.json"] = write(output, f"{target}.json", packet)
            candidate = dict(schema_version=1, case_id=case["case_id"], coefficient_unit="m",
                             parameter_names=parameter_names(),
                             base_coefficients=snapshot["base_coefficients"])
            files[f"{target}-candidate.json"] = write(output, f"{target}-candidate.json", candidate)
            expected = dict(
                target_id=target, snapshot_sha256=manifest[snapshot_name],
                packet_sha256=files[f"{target}.json"],
                candidate_sha256=files[f"{target}-candidate.json"],
                original_current_A=max(abs(row["current"]) for row in snapshot["physical"]),
                native_B_T=arrays["inner_B"].tolist(),
                original_metrics=json.loads((root / target / "fit/interior/level-2.json")
                                            .read_bytes())["metrics"],
            )
            write(controls, f"{target}-native.json", expected)
    write(output, "manifest.json", dict(schema_version=1, packet_id="clear-coil-interior-v1",
                                       files=files))
    assert time.monotonic() - start < 30, "Export exceeded 30 s"
    assert shutil.disk_usage(output).free >= 2 * 1024**3, "2 GiB reserve required"
    print(json.dumps(dict(files=files, source_manifest_entries=len(manifest),
                          elapsed_s=time.monotonic() - start), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--controls", required=True, type=Path)
    args = parser.parse_args()
    export(args.archive, args.output, args.controls)
