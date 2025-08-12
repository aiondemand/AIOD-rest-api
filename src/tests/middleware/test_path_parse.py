import pytest
from middleware.path_parse import parse_asset_from_path

@pytest.mark.parametrize("path,expected", [
    # full path (no version here)
    ("/datasets/abc",                     ("datasets", "datasets/abc")),
    ("/datasets/v1/1",                    ("datasets", "datasets/v1/1")),
    ("/datasets/abc/",                    ("datasets", "datasets/abc")),
    # versioned API / deployment prefix
    ("/v2/datasets/abc",                  ("datasets", "v2/datasets/abc")),
    ("/aiod-api/v10/models/bert",         ("models", "v10/models/bert")),
    ("/aiod-api/models/bert",             ("models", "models/bert")),
    # non-asset / excluded
    ("/metrics",                          None),
    ("/docs",                             None),
    ("/v2/docs",                          None),
    ("/counts/v1",                        None),
    ("/",                                 None),
])
def test_parse_asset_from_path(path, expected):
    assert parse_asset_from_path(path) == expected
