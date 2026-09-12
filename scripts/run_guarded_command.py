"""Record one explicitly requested command under the existing disk-reserve guard."""

import argparse
import json
import os
import sys
from pathlib import Path

from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.resource_guard import GIB, guarded_run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or args.output.exists():
        raise ValueError("explicit nonempty command and new output directory required")
    root = Path(__file__).resolve().parents[1]
    args.output.mkdir(parents=True)
    log = args.output / "command.log"
    record = dict(
        repository=git_state(root),
        command=command,
        status="running",
        source=dict(path=str(Path(__file__).resolve()), sha256=sha256_file(Path(__file__))),
    )
    output = args.output / "summary.json"
    try:
        write_json_atomic(output, record)
        with log.open("xb") as stream:
            record.update(
                guarded_run(
                    command,
                    cwd=root,
                    env=os.environ,
                    stdout=stream,
                    space_root=root,
                    reserve_bytes=2 * GIB,
                )
            )
        record.update(status="completed" if record["returncode"] == 0 else "command_failed")
    except Exception as error:
        record.update(status="error", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        active_error = sys.exc_info()[0] is not None
        try:
            if log.exists():
                record["log"] = dict(path=str(log.resolve()), sha256=sha256_file(log))
            write_json_atomic(output, record)
        except OSError as error:
            print(f"Command checkpoint failed: {error}", file=sys.stderr)
            if not active_error:
                raise
    print(json.dumps({"status": record["status"], "returncode": record["returncode"]}))
    return record["returncode"]


if __name__ == "__main__":
    raise SystemExit(main())
