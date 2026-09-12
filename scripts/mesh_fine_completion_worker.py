"""The unchanged single finest mesh with newly preregistered4M work cap."""

import argparse
from pathlib import Path

from mesh_nonlocal_inputs import frozen_inputs, load_mesh

from fusion_baselines.mesh_nonlocal_scan import reference, scan
from fusion_baselines.provenance import write_json_atomic


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new finest-mesh worker paths required")
    root = Path(__file__).resolve().parents[1]
    source, original = frozen_inputs(root)
    row = original["meshes"][5]
    report = dict(status="running", mesh=row["mesh"], intrinsic_source=reference(source),
                  code=reference(Path(__file__)), nonlocal_screen_pass=False)
    write_json_atomic(args.output, report)
    try:
        points, cells, tags = load_mesh(row["mesh"])
        result = scan(points, cells, tags, args.raw, max_seconds=1200, max_sat_pairs=4000000)
        report.update(status="completed", scan=reference(args.raw/"summary.json"),
                      complete_scan=result["complete"],
                      nonlocal_screen_pass=result["nonlocal_screen_pass"])
    except Exception as error:
        report.update(status="error", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json_atomic(args.output, report)
    return 0 if report["nonlocal_screen_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
