"""Package metadata and import tests."""

import re

import pysos_rpr

SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)


def test_package_imports():
    assert pysos_rpr.__name__ == "pysos_rpr"
    assert "__version__" in pysos_rpr.__all__


def test_version_is_semver():
    assert SEMVER.match(pysos_rpr.__version__), pysos_rpr.__version__


def test_version_matches_release():
    assert pysos_rpr.__version__ == "0.1.0"
