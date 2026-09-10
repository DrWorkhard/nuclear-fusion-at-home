import hashlib
import stat
from zipfile import ZipFile, ZipInfo

import pytest

from fusion_baselines.qi_archive import extract_verified_members, finite_beta_cases


def archive(tmp_path, entries):
    path = tmp_path / "test.zip"
    with ZipFile(path, "w") as zipped:
        for name, content in entries:
            zipped.writestr(name, content)
    return path, hashlib.md5(path.read_bytes()).hexdigest()


def test_inventory_selection():
    cases = finite_beta_cases()
    assert len(cases) == 31
    assert len({c["wout_member"] for c in cases}) == 31
    assert cases[0]["input_member"].endswith("input.QI_nfp1_beta1")
    assert cases[-1]["filename_beta_percent"] == 3.75


def test_verified_extract_and_no_overwrite(tmp_path):
    path, md5 = archive(tmp_path, [("one/data", b"hello"), ("unselected", b"ignore")])
    target = tmp_path / "out"
    result = extract_verified_members(path, target, ["one/data"], expected_md5=md5)
    assert (target / "one/data").read_bytes() == b"hello"
    assert not (target / "unselected").exists()
    assert result["members"]["one/data"]["sha256"] == hashlib.sha256(b"hello").hexdigest()
    with pytest.raises(FileExistsError):
        extract_verified_members(path, target, ["one/data"], expected_md5=md5)


@pytest.mark.parametrize("members,md5_override", [
    (["../escape"], None), (["/absolute"], None), (["one//data"], None),
    (["missing"], None), (["one/data", "one/data"], None), (["one/data"], "wrong"),
])
def test_rejected_before_writing(tmp_path, members, md5_override):
    path, md5 = archive(tmp_path, [("one/data", b"hello")])
    target = tmp_path / "out"
    with pytest.raises(ValueError):
        extract_verified_members(path, target, members, expected_md5=md5_override or md5)
    assert not target.exists()


def test_reject_symlink_member(tmp_path):
    info = ZipInfo("link")
    info.create_system = 3
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    path, md5 = archive(tmp_path, [(info, b"elsewhere")])
    with pytest.raises(ValueError, match="not a regular file"):
        extract_verified_members(path, tmp_path / "out", ["link"], expected_md5=md5)
