import tomllib

from config import _merge_configurations

DEFAULT_CONFIG = """
[section1]
integer = 2
string = "hello"

[section1.subsection]
float = 3.2
array = [1, 2, 3]

[section2]
integer = 42
"""


def test_merge_configuration_no_override_means_no_change():
    default = tomllib.loads(DEFAULT_CONFIG)
    merged = _merge_configurations(default, override={})
    assert default == merged


def test_merge_configuration_nonnested():
    default = tomllib.loads(DEFAULT_CONFIG)
    override_text = """
    [section1]
    integer = 0
    """
    override = tomllib.loads(override_text)

    merged = _merge_configurations(default, override)
    assert merged["section1"]["integer"] == 0

    del merged["section1"]["integer"]
    del default["section1"]["integer"]
    assert default == merged


def test_merge_configuration_nested():
    default = tomllib.loads(DEFAULT_CONFIG)
    override_text = """
    [section1.subsection]
    float = 1.0
    """
    override = tomllib.loads(override_text)

    merged = _merge_configurations(default, override)
    assert merged["section1"]["subsection"]["float"] == 1.0

    del merged["section1"]["subsection"]["float"]
    del default["section1"]["subsection"]["float"]
    assert default == merged


def test_merge_configuration_array():
    default = tomllib.loads(DEFAULT_CONFIG)
    override_text = """
    [section1.subsection]
    array = [0,3,7]
    """
    override = tomllib.loads(override_text)

    merged = _merge_configurations(default, override)
    assert merged["section1"]["subsection"]["array"] == [0, 3, 7]

    del merged["section1"]["subsection"]["array"]
    del default["section1"]["subsection"]["array"]
    assert default == merged
