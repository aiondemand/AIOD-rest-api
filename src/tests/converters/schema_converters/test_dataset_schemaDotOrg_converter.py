import pytest

from converters.schema_converters import dataset_converter_schema_dot_org_instance
from database.model.dataset.dataset import Dataset
from tests.testutils.paths import path_test_resources


@pytest.mark.skip(reason="TODO: while going to Metadata model v2")
def test_aiod_to_schema_dot_org_happy_path(dataset: Dataset):
    converter = dataset_converter_schema_dot_org_instance
    result = converter.convert(dataset)
    actual = result.json(by_alias=True, indent=4)
    with open(path_test_resources() / "schemes" / "schema_dot_org" / "dataset.json", "r") as f:
        expected = f.read()
    for i, (row_actual, row_expected) in enumerate(zip(actual.split("\n"), expected.split("\n"))):
        assert row_actual == row_expected, f"Line {i}: {row_actual} != {row_expected}"
    assert actual == expected
