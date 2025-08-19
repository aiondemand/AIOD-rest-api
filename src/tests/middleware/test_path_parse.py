import pytest
from middleware.path_parse import parse_asset_from_path

@pytest.mark.parametrize("path,expected", [
    # typed routes (asset_id has no API version prefix and no type prefix)
    ("/datasets/abc",                     ("datasets", "abc")),
    ("/datasets/v1/1",                    ("datasets", "v1/1")),
    ("/datasets/abc/",                    ("datasets", "abc")),
    ("/v2/datasets/abc",                  ("datasets", "abc")),
    ("/aiod-api/v10/models/bert",         ("models", "bert")),
    ("/aiod-api/models/bert",             ("models", "bert")),

    # generic asset routes
    ("/assets/datasets/123",              ("datasets", "123")),
    ("/assets/models:bert",               ("models", "bert")),

    # non-asset / excluded
    ("/metrics",                          None),
    ("/docs",                             None),
    ("/v2/docs",                          None),
    ("/counts/v1",                        None),
    ("/",                                 None),
])
def test_parse_asset_from_path(path, expected):
    assert parse_asset_from_path(path) == expected
