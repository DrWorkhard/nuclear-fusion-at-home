"""Narrow, non-overwriting extraction of the Goodman finite-pressure cases."""

import hashlib
import shutil
import stat
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

from fusion_baselines.provenance import sha256_file

GOODMAN_MD5 = "f6983a41403da28247025be631522caa"


def finite_beta_cases():
    cases = []
    for nfp in (1, 2, 3):
        for quarter in ([4] if nfp == 1 else range(1, 16)):
            beta = quarter / 4
            stem = "QI_nfp1_beta1" if nfp == 1 else f"nfp{nfp}_beta_{beta:.2f}"
            prefix = f"Files/configurations/nfp{nfp}/beta/"
            cases.append({
                "case": stem,
                "nfp": nfp,
                "filename_beta_percent": beta,
                "input_member": prefix + "input." + stem,
                "wout_member": prefix + "wout_" + stem + ".nc",
            })
    return cases


def extract_verified_members(archive: Path, target: Path, members, *, expected_md5: str):
    """Require a fresh target and verify all selected members before any writes.

    The MD5 identifies the published release, not a cryptographic authority proof.
    SHA-256 records bind the archive and every extracted file for later reuse.
    """
    if target.exists() or target.is_symlink():
        raise FileExistsError(target)
    members = list(members)
    if not members or len(set(members)) != len(members):
        raise ValueError("empty or duplicate selection")
    for member in members:
        path = PurePosixPath(member)
        if path.is_absolute() or ".." in path.parts or str(path) != member:
            raise ValueError("unsafe archive member")
    with archive.open("rb") as stream:
        actual_md5 = hashlib.file_digest(stream, "md5").hexdigest()
    if actual_md5 != expected_md5:
        raise ValueError("archive MD5 mismatch")
    records = {}
    with ZipFile(archive) as zipped:
        names = zipped.namelist()
        for member in members:
            if names.count(member) != 1:
                raise ValueError(f"missing or duplicate archive entry: {member}")
            info = zipped.getinfo(member)
            mode = stat.S_IFMT(info.external_attr >> 16)
            if info.is_dir() or mode not in (0, stat.S_IFREG):
                raise ValueError(f"not a regular file: {member}")
            with zipped.open(info) as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            records[member] = {"bytes": info.file_size, "sha256": digest}
        target.mkdir(parents=True, exist_ok=False)
        for member in members:
            output = target / member
            output.parent.mkdir(parents=True, exist_ok=True)
            with zipped.open(member) as source, output.open("xb") as destination:
                shutil.copyfileobj(source, destination)
            if sha256_file(output) != records[member]["sha256"]:
                raise ValueError(f"post-extraction hash mismatch: {member}")
    return {"md5": actual_md5, "sha256": sha256_file(archive), "members": records}
