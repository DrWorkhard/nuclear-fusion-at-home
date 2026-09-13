import hashlib
import io
import sys
import tarfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_netcdf_source_declarations import MEMBERS, archive_contents, snippets


def archive(duplicate=False, symlink=False):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as handle:
        for name in [*MEMBERS, *([MEMBERS[0]] if duplicate else [])]:
            data = b"example\n"
            member = tarfile.TarInfo(name)
            member.size = len(data)
            if symlink:
                member.type, member.linkname = tarfile.SYMTYPE, "/irrelevant/not/read"
            handle.addfile(member, io.BytesIO(data))
    data = stream.getvalue()
    return data, hashlib.sha256(data).hexdigest()


def test_exact_bounded_archive_read_without_extraction():
    data, sha = archive()
    assert archive_contents(data, sha) == dict.fromkeys(MEMBERS, b"example\n")
    assert snippets(b"other\nneedle\n", ("needle",)) == [dict(line=2, text="needle")]
    with pytest.raises(ValueError, match="hash"):
        archive_contents(data, "0" * 64)


@pytest.mark.parametrize("option", ["duplicate", "symlink"])
def test_ambiguous_or_nonregular_source_members_rejected(option):
    data, sha = archive(**{option: True})
    with pytest.raises(ValueError, match="unique|ordinary"):
        archive_contents(data, sha)
