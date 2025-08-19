import pytest

from versioning import Version

pytest_plugins = ["tests.testutils.default_instances", "tests.testutils.default_sqlalchemy"]


def pytest_generate_tests(metafunc):
    # We want to automatically test endpoints on all supported versions,
    # and allow version-specific tests to be written using a
    # @pytest.mark.versions("vX") marker
    if "client" in metafunc.fixturenames:
        default_versions = (Version.LATEST, Version.V3)
        version_marker = next((m for m in metafunc.definition.own_markers if m.name == "versions"), None)
        selected_versions = version_marker.args if version_marker else default_versions

        # If version is set through the command line, only use that for testing.
        all_versions = list(Version)
        versions_to_include = metafunc.config.getoption("versions") or all_versions
        versions = set(selected_versions).intersection(set(versions_to_include))
        if not versions:
            pytest.skip(f"Test not defined for selection: {versions_to_include}")

        metafunc.parametrize(
            "client", versions, indirect=True
        )


def pytest_addoption(parser):
    parser.addoption(
        "--versions",
        action="append",
        default=[],
        help="list of versions for which to run tests",
    )
