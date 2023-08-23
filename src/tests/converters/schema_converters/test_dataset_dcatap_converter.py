import pytest

from converters.schema_converters import dataset_converter_dcatap_instance
from database.model.dataset.dataset import Dataset
from tests.testutils.paths import path_test_resources


@pytest.mark.skip(reason="TODO: while going to Metadata model v2")
def test_aiod_to_dcatap_happy_path(dataset: Dataset):
    converter = dataset_converter_dcatap_instance
    dcat_ap = converter.convert(dataset)
    actual = dcat_ap.json(by_alias=True, indent=4)
    with open(path_test_resources() / "schemes" / "dcatap" / "dataset.json", "r") as f:
        expected = f.read()
    for i, (row_actual, row_expected) in enumerate(zip(actual.split("\n"), expected.split("\n"))):
        assert row_actual == row_expected, f"Line {i}: {row_actual} != {row_expected}"
    assert actual == expected
