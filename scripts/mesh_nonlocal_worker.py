"""One original mesh, unchanged coordinates, bounded certificate-producing scan."""

import argparse
import json
from pathlib import Path

import meshio
import numpy as np
from mesh_nonlocal_inputs import frozen_inputs, load_mesh, source_code_bindings

from fusion_baselines.mesh_nonlocal_scan import reference, scan
from fusion_baselines.provenance import write_json_atomic


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("index", type=int, choices=range(6))
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new immutable mesh worker paths required")
    root = Path(__file__).resolve().parents[1]
    source_path, source = frozen_inputs(root)
    original = source["meshes"][args.index]
    report = dict(status="running", index=args.index, target_h_m=original["target_h_m"],
                  mesh=original["mesh"], intrinsic_source=reference(source_path),
                  historical_source_code=source_code_bindings(root, source),
                  code=reference(Path(__file__)), nonlocal_screen_pass=False,
                  versions=dict(numpy=np.__version__, meshio=meshio.__version__))
    write_json_atomic(args.output, report)
    try:
        points, cells, tags = load_mesh(original["mesh"])
        result = scan(points, cells, tags, args.raw, max_seconds=1200, max_sat_pairs=2000000)
        report.update(status="completed", complete_scan=result["complete"],
                      nonlocal_screen_pass=result["nonlocal_screen_pass"],
                      scan=reference(args.raw / "summary.json"))
    except Exception as error:
        report.update(status="error", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json_atomic(args.output, report)
    print(json.dumps({"index": args.index, "status": report["status"],
                      "nonlocal_screen_pass": report["nonlocal_screen_pass"]}), flush=True)
    return 0 if report["nonlocal_screen_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
