import pytest
from middleware.path_parse import parse_asset_from_path

@pytest.mark.parametrize("path,expected", [
    # typed routes (asset_id has no API version prefix and no type prefix)
    ("/datasets/data_foobar12foobar12foobar12",           ("datasets", "data_foobar12foobar12foobar12")),
    ("/datasets/data_foobar12foobar12foobar12/",          ("datasets", "data_foobar12foobar12foobar12")),
    ("/v2/datasets/data_foobar12foobar12foobar12",        ("datasets", "data_foobar12foobar12foobar12")),

    # generic asset routes
    ("/assets/data_foobar12foobar12foobar12",             ("datasets", "data_foobar12foobar12foobar12")),
    ("/assets/proj_foobar12foobar12foobar12",             ("projects", "proj_foobar12foobar12foobar12")),

    # non-asset / excluded
    ("/metrics",                     None),
    ("/docs",                        None),
    ("/v2/docs",                     None),
    ("/counts/v1",                   None),
    ("/",                            None),
])
def test_parse_asset_from_path(path, expected):
    assert parse_asset_from_path(path) == expected


@pytest.mark.parametrize("path,expected", [
    ("/aiod-api/v10/ml_models/mdl_foobar12foobar12foobar12",         ("ml_models", "mdl_foobar12foobar12foobar12")),
    ("/aiod-api/ml_models/mdl_foobar12foobar12foobar12",             ("ml_models", "mdl_foobar12foobar12foobar12")),
    ("/aiod-api/assets/mdl_foobar12foobar12foobar12",             ("ml_models", "mdl_foobar12foobar12foobar12")),
])
def test_parse_asset_from_path_with_prefix(path, expected):
    from config import DEV_CONFIG
    DEV_CONFIG['url_prefix'] = 'aiod-api'
    assert parse_asset_from_path(path) == expected
