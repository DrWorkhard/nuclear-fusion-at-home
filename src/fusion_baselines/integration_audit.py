"""Fail-closed check of the fixed six-test QI/W7-X integration report."""

from xml.etree import ElementTree

EXPECTED_CASES = {
    ("tests.test_scientific_integration", "test_real_goodman_metadata[qi-goodman-2022.json]"),
    ("tests.test_scientific_integration", "test_real_goodman_metadata[qi-goodman-2022-nfp2.json]"),
    ("tests.test_scientific_integration", "test_w7x_corrected_tolerances_and_retained_failures"),
    *(
        ("tests.test_qi_data_integration", f"test_frozen_real_data_actions[nfp{i}]")
        for i in (1, 2, 3)
    ),
}


def audit_integration_xml(path):
    root = ElementTree.parse(path).getroot()
    cases = list(root.iter("testcase"))
    keys = [(case.get("classname"), case.get("name")) for case in cases]
    checks = {
        "exact_test_set": set(keys) == EXPECTED_CASES,
        "no_duplicates": len(keys) == len(set(keys)) == len(EXPECTED_CASES),
        "no_skips": not list(root.iter("skipped")),
        "no_failures": not list(root.iter("failure")),
        "no_errors": not list(root.iter("error")),
    }
    return dict(checks=checks, test_count=len(cases), all_pass=all(checks.values()))
