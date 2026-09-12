from xml.etree import ElementTree

import pytest

from fusion_baselines.integration_audit import EXPECTED_CASES, audit_integration_xml


@pytest.mark.parametrize("variable", ["FUSION_REQUIRE_QI_DATA", "FUSION_REQUIRE_W7X_DATA"])
def test_missing_fixtures_fail_only_in_required_mode(
    tmp_path, monkeypatch, scientific_files, variable
):
    path = tmp_path / "missing.nc"
    monkeypatch.delenv(variable, raising=False)
    with pytest.raises(pytest.skip.Exception, match="missing.nc"):
        scientific_files([path], variable)
    monkeypatch.setenv(variable, "1")
    with pytest.raises(pytest.fail.Exception, match="missing.nc"):
        scientific_files([path], variable)
    path.write_bytes(b"fixture")
    scientific_files([path], variable)


@pytest.mark.parametrize("mutation", [None, "skipped", "failure", "error", "missing", "duplicate"])
def test_integration_report_rejects_incomplete_or_failed_runs(tmp_path, mutation):
    root = ElementTree.Element("testsuites")
    suite = ElementTree.SubElement(root, "testsuite")
    for classname, name in sorted(EXPECTED_CASES):
        ElementTree.SubElement(suite, "testcase", classname=classname, name=name)
    if mutation in {"skipped", "failure", "error"}:
        ElementTree.SubElement(suite[0], mutation)
    elif mutation == "missing":
        suite.remove(suite[0])
    elif mutation == "duplicate":
        ElementTree.SubElement(suite, "testcase", **suite[0].attrib)
    path = tmp_path / "report.xml"
    ElementTree.ElementTree(root).write(path)
    assert audit_integration_xml(path)["all_pass"] is (mutation is None)
