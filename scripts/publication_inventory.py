"""Read-only inventory of tracked/reachable Git data before public release.

Run from the repository root. Outputs counts and credential-shaped match locations,
never matched values. Limited patterns, not a complete security or rights audit.
Scans committed objects only; ignored/untracked files and commit messages are not
credential-scanned. Does not rewrite history, remove files, or approve publication.
"""

import collections
import hashlib
import json
import re
import subprocess


def git(*args):
    return subprocess.check_output(["git", *args])


def main():
    revision = git("rev-parse", "HEAD").decode().strip()
    head = {}
    head_sizes = {}
    for row in git("ls-tree", "-r", "-l", "-z", "HEAD").split(b"\0"):
        if not row:
            continue
        metadata, path = row.split(b"\t", 1)
        mode, kind, oid, size = metadata.split()
        if kind == b"blob":
            key = oid.decode()
            head.setdefault(key, []).append(path.decode())
            head_sizes[path.decode()] = int(size)

    objects = {}
    for row in git("rev-list", "--objects", "--all").splitlines():
        oid, _, name = row.partition(b" ")
        objects[oid.decode()] = name.decode(errors="replace")
    metadata = subprocess.run(
        ["git", "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
        input=("\n".join(objects) + "\n").encode(), stdout=subprocess.PIPE, check=True
    ).stdout.splitlines()
    blobs = {}
    kinds = collections.Counter()
    for row in metadata:
        oid, kind, size = row.decode().split()
        kinds[kind] += 1
        if kind == "blob":
            blobs[oid] = int(size)

    rules = {
        "private_key_banner": (
            rb"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY(?: BLOCK)?-----"
        ),
        "github_credential_shape": (
            rb"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{70,})\b"
        ),
        "openai_credential_shape": rb"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}\b",
        "aws_access_id_shape": rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
        "credential_url_shape": rb"https?://[^\s/@:]+:[^/@\s]{8,}@",
        "unix_home_path": rb"/(?:Users|home)/[A-Za-z0-9._-]+/",
        "windows_home_path": rb"[A-Za-z]:\\+Users\\+[^\\\r\n\x22]+\\+",
    }
    patterns = {name: re.compile(value) for name, value in rules.items()}
    synthetic = {
        "private_key_banner": b"-----BEGIN " + b"PRIVATE KEY-----",
        "github_credential_shape": b"ghp_" + b"A" * 36,
        "openai_credential_shape": b"sk-" + b"B" * 32,
        "aws_access_id_shape": b"AKIA" + b"C" * 16,
        "credential_url_shape": b"https://" + b"example:placeholder-password@example.invalid",
        "unix_home_path": b"/Users/" + b"example/workspace/",
        "windows_home_path": (
            b"C:" + bytes([92]) + b"Users" + bytes([92]) + b"example" + bytes([92])
        ),
    }
    for name, pattern in patterns.items():
        assert pattern.search(synthetic[name]), name
        assert not pattern.search(b"ordinary unremarkable text"), name

    matches = {name: [] for name in patterns}
    reader = subprocess.Popen(
        ["git", "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE
    )
    for oid, size in blobs.items():
        reader.stdin.write((oid + "\n").encode())
        reader.stdin.flush()
        object_id, kind, count = reader.stdout.readline().split()
        assert object_id.decode() == oid and kind == b"blob" and int(count) == size
        payload = reader.stdout.read(size)
        assert len(payload) == size and reader.stdout.read(1) == b"\n"
        for name, pattern in patterns.items():
            if pattern.search(payload):
                matches[name].append(oid)
    reader.stdin.close()
    assert reader.wait() == 0
    assert git("rev-parse", "HEAD").decode().strip() == revision
    identities = set()
    for line in git("log", "--all", "--format=%ae%x00%ce").splitlines():
        identities.update(line.split(b"\0"))
    identities.discard(b"")
    head_counts = {
        name: sum(len(head.get(oid, [])) for oid in hits)
        for name, hits in matches.items()
    }
    secret_names = [
        name for name in rules if name.endswith("shape") or name == "private_key_banner"
    ]
    print(json.dumps({
        "schema_version": 1,
        "kind": "bounded-publication-inventory",
        "source_revision": revision,
        "scope": "HEAD tracked files and unique blobs reachable from all local refs",
        "reachable_object_counts": dict(kinds),
        "reachable_blob_bytes_scanned": sum(blobs.values()),
        "head_tracked_files": len(head_sizes),
        "head_tracked_blob_bytes": sum(head_sizes.values()),
        "largest_blob_bytes": max(blobs.values()),
        "blob_count_over_10MiB": sum(n > 10 * 1024**2 for n in blobs.values()),
        "blob_count_over_50MiB": sum(n > 50 * 1024**2 for n in blobs.values()),
        "regex_selftests": {"positive": len(patterns), "negative": len(patterns), "passed": True},
        "patterns": {name: value.decode() for name, value in rules.items()},
        "matched_reachable_blob_counts": {name: len(hits) for name, hits in matches.items()},
        "matched_head_file_counts": head_counts,
        "credential_shape_locations": {
            name: [
                {"oid": oid, "path": objects[oid], "present_at_head": oid in head}
                for oid in matches[name]
            ]
            for name in secret_names if matches[name]
        },
        "head_home_path_counts_by_directory": dict(collections.Counter(
            path.split("/")[0]
            for oid in set(matches["unix_home_path"] + matches["windows_home_path"])
            for path in head.get(oid, [])
        )),
        "distinct_commit_author_or_committer_emails": len(identities),
        "matched_values_disclosed": False,
        "ignored_or_untracked_files_scanned": False,
        "commit_messages_scanned_for_credentials": False,
        "encoded_or_compressed_payloads_decoded": False,
        "provider_exhaustive_secret_scan": False,
        "license_rights_clearance": False,
        "publication_approved": False,
        "reference_manifest_sha256": hashlib.sha256(git("show-ref")).hexdigest(),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
