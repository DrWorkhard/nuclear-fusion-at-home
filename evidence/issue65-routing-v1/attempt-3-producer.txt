"""Locate one frozen coil ID using bounded Parquet ID-column reads, not full shards."""
import argparse
import hashlib
import io
import json
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVISION = '286a268c664938519af6ceacfb4ec8143f64e20e'
SELECTED = 'DRSySxvjUFWt5VLxPVRW37N'


def main(reader, tree_path, output):
    assert not output.exists()
    assert shutil.disk_usage(output.parent).free >= 3*1024**3
    assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT)
    producer = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    output.mkdir()
    start = time.monotonic()
    report = dict(completed=False, producer=producer, dataset_revision=REVISION,
                  selected_id=SELECTED, physical_admission=False, requests=[], downloaded_bytes=0)
    tree = {r['path']: r for r in json.loads(tree_path.read_text(encoding='utf-8'))}
    paths = [f'coilsets/part-{n}.parquet' for n in range(3)]
    cache = {}

    def guard():
        assert time.monotonic()-start < 180, '180 s attempt ceiling'
        assert report['downloaded_bytes'] <= 32*1024**2, '32 MiB additional data ceiling'
        assert len(report['requests']) <= 60, '60 range requests ceiling'
        assert shutil.disk_usage(output).free >= 2*1024**3, '2 GiB live reserve'

    def fetch(path, offset, length):
        key = (path, offset, length)
        if key in cache:
            return cache[key].read_bytes()
        guard()
        assert 0 < length <= 16*1024**2
        assert report['downloaded_bytes']+length <= 32*1024**2
        assert len(report['requests']) < 60
        size = tree[path]['size']
        end = offset+length-1
        assert 0 <= offset <= end < size
        index = len(report['requests'])
        data = output/f'range-{index:03d}.bin'
        headers = output/f'range-{index:03d}.headers'
        url = ('https://huggingface.co/datasets/proxima-fusion/coilstellaration/resolve/'
               +REVISION+'/'+path)
        entry = dict(path=path, offset=offset, length=length, url=url, completed=False)
        report['requests'].append(entry)
        command = ['curl', '--silent', '--show-error', '--fail', '--location',
                   '--max-time', str(min(30, max(1, int(180-(time.monotonic()-start))))),
                   '--max-filesize', str(length), '--range', f'{offset}-{end}',
                   '--dump-header', str(headers), url, '-o', str(data)]
        child = subprocess.run(command, capture_output=True, text=True, timeout=32)
        entry.update(returncode=child.returncode, stderr=child.stderr)
        report['downloaded_bytes'] += data.stat().st_size if data.exists() else 0
        assert child.returncode == 0, child.stderr
        received = data.read_bytes()
        assert len(received) == length, 'range length mismatch'
        header_text = headers.read_text(encoding='utf-8').lower()
        assert f'content-range: bytes {offset}-{end}/{size}' in header_text
        entry.update(completed=True, sha256=hashlib.sha256(received).hexdigest())
        cache[key] = data
        guard()
        return received

    sys.path.insert(0, str(reader))
    import duckdb
    from fsspec import AbstractFileSystem

    class RangeFile(io.RawIOBase):
        def __init__(self, path):
            self.path, self.pos = path, 0

        def readable(self):
            return True

        def seekable(self):
            return True

        def tell(self):
            return self.pos

        def seek(self, offset, whence=0):
            self.pos = [0, self.pos, tree[self.path]['size']][whence]+offset
            assert 0 <= self.pos <= tree[self.path]['size']
            return self.pos

        def read(self, length=-1):
            available = tree[self.path]['size']-self.pos
            length = available if length < 0 else min(length, available)
            if length == 0:
                return b''
            data = fetch(self.path, self.pos, length)
            self.pos += length
            return data

    class Ranges(AbstractFileSystem):
        protocol = 'bounded'

        def modified(self, path):
            self.info(path)
            # Cache sentinel for frozen URLs, not a claimed upstream modification time.
            return datetime(1970, 1, 1, tzinfo=UTC)

        def info(self, path, **kwargs):
            path = self._strip_protocol(path)
            assert path in paths, 'only three pinned shards permitted'
            return dict(name=path, size=tree[path]['size'], type='file')

        def _open(self, path, mode='rb', **kwargs):
            assert mode == 'rb'
            self.info(path)
            return RangeFile(self._strip_protocol(path))

    try:
        connection = duckdb.connect(config=dict(threads=1, memory_limit='128MB',
                                               autoload_known_extensions=False,
                                               autoinstall_known_extensions=False))
        connection.register_filesystem(Ranges())
        counts = [connection.execute('SELECT num_rows FROM parquet_file_metadata(?)',
                                     ['bounded://'+path]).fetchone()[0] for path in paths]
        matches = connection.execute(
            'SELECT id, file_row_number FROM read_parquet(?, file_row_number=true) WHERE id = ?',
            ['bounded://'+paths[2], SELECTED]).fetchall()
        assert len(matches) == 1
        report.update(completed=True, shard_row_counts=counts, selected_shard_row=matches[0][1],
                      proposed_api_row=sum(counts[:2])+matches[0][1],
                      api_row_identity_verified=False, full_shard_hash_verified=False)
        guard()
    except Exception as error:
        report.update(completed=False, error=f'{type(error).__name__}: {error}')
    report.update(elapsed_s=time.monotonic()-start, duckdb_version=duckdb.__version__,
                  tree_sha256=hashlib.sha256(tree_path.read_bytes()).hexdigest(),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (output/'lookup.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'requests'}, indent=2))
    return 0 if report['completed'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reader', type=Path, required=True)
    parser.add_argument('--tree', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(main(args.reader.resolve(), args.tree.resolve(), args.output.resolve()))
