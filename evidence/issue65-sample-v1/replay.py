"""Verify the scoped archive then replay the saved arithmetic without fetching data."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(expected):
    assert digest(HERE/'manifest.json') == expected
    manifest = json.loads((HERE/'manifest.json').read_text(encoding='utf-8'))
    for name, sha in manifest.items():
        assert digest(ROOT/name) == sha, name
    original = json.loads((HERE/'inspection.json').read_text(encoding='utf-8'))
    for name, sha in original['source_hashes'].items():
        assert digest(ROOT/name) == sha, name
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory)/'inspection.json'
        subprocess.run([sys.executable, '-I', '-S', '-B',
                        str(ROOT/'scripts/inspect_community_sample.py'), '--output', str(output)],
                       check=True, timeout=30, capture_output=True)
        replay = json.loads(output.read_text(encoding='utf-8'))
    original.pop('producer')
    replay.pop('producer')
    assert replay == original
    print(json.dumps(dict(manifest_files=len(manifest),
                          arithmetic_checks=len(replay['arithmetic_checks']),
                          partial_intake_reproduced=True, geometry_or_field_replayed=False)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest-sha', required=True)
    main(parser.parse_args().manifest_sha)
