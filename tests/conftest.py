"""Shared missing-data policy: optional core tests, fail-closed scientific runs."""

import os

import pytest


@pytest.fixture
def scientific_files():
    def check(paths, required_variable):
        missing = [str(path) for path in paths if not path.is_file()]
        if not missing:
            return
        message = "scientific fixtures missing: " + ", ".join(missing)
        if os.environ.get(required_variable) == "1":
            pytest.fail(message)
        pytest.skip(message)

    return check
