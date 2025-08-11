# src/tests/test_path_parse.py
import pytest
from middleware.path_parse import parse_asset_from_path

@pytest.mark.parametrize("path,expected", [
    ("/datasets/abc",                     ("datasets", "abc")),
    ("/datasets/v1/1",                    ("datasets", "v1/1")),
    ("/v2/datasets/abc",                  ("datasets", "abc")),
    ("/aiod-api/v10/models/bert",         ("models", "bert")),
    ("/aiod-api/models/bert",             ("models", "bert")),
    ("/metrics",                          None),
    ("/docs",                             None),
    ("/counts/v1",                        None),
    ("/",                                 None),
])
def test_parse_asset_from_path(path, expected):
    assert parse_asset_from_path(path) == expected
