import json

import responses

from connectors.huggingface.huggingface_dataset_connector import HuggingFaceDatasetConnector
from connectors.resource_with_relations import ResourceWithRelations
from database.model.ai_resource.text import Text
from database.model.platform.platform_names import PlatformName
from tests.testutils.paths import path_test_resources

HUGGINGFACE_URL = "https://datasets-server.huggingface.co"


def test_fetch_all_happy_path():
    ids_expected = {
        "0n1xus/codexglue",
        "04-07-22/wep-probes",
        "rotten_tomatoes",
        "acronym_identification",
        "air_dialogue",
        "bobbydylan/top2k",
    }
    connector = HuggingFaceDatasetConnector()
    with responses.RequestsMock() as mocked_requests:
        path_data_list = path_test_resources() / "connectors" / "huggingface" / "data_list.json"
        with open(path_data_list, "r") as f:
            response = json.load(f)
        mocked_requests.add(
            responses.GET,
            "https://huggingface.co/api/datasets?full=True",
            json=response,
            status=200,
        )
        for dataset_id in ids_expected:
            mock_parquet(mocked_requests, dataset_id)
        resources_with_relations = list(connector.fetch())

    assert len(resources_with_relations) == len(ids_expected)
    assert all(type(r) == ResourceWithRelations for r in resources_with_relations)

    datasets = [r.resource for r in resources_with_relations]
    assert {d.platform_resource_identifier for d in datasets} == ids_expected
    assert {d.name for d in datasets} == ids_expected
    assert all(d.date_published for d in datasets)
    assert all(d.aiod_entry for d in datasets)

    assert all(len(r.related_resources) in (1, 2) for r in resources_with_relations)
    assert all(len(r.related_resources["citation"]) == 1 for r in resources_with_relations[:5])

    dataset = datasets[0]
    assert dataset.platform_resource_identifier == "acronym_identification"
    assert dataset.platform == PlatformName.huggingface
    assert dataset.description == Text(
        plain="Acronym identification training and development "
        "sets for the acronym identification task at SDU@AAAI-21."
    )
    assert dataset.name == "acronym_identification"
    assert dataset.same_as == "https://huggingface.co/datasets/acronym_identification"
    assert dataset.license == "mit"
    assert len(dataset.distribution) == 3
    expected_url_base = (
        "https://huggingface.co/datasets/acronym_identification/resolve"
        "/refs%2Fconvert%2Fparquet/default/"
    )
    assert {dist.content_url for dist in dataset.distribution} == {
        (expected_url_base + "acronym_identification-test.parquet"),
        (expected_url_base + "acronym_identification-train.parquet"),
        (expected_url_base + "acronym_identification-validation.parquet"),
    }
    assert dataset.is_accessible_for_free
    assert set(dataset.keyword) == {
        "acronym-identification",
        "annotations_creators:expert-generated",
        "arxiv:2010.14678",
        "language:en",
        "language_creators:found",
        "license:mit",
        "multilinguality:monolingual",
        "region:us",
        "size_categories:10K<n<100K",
        "source_datasets:original",
        "task_categories:token-classification",
    }


def test_incorrect_citation():
    """
    Many datasets have an incorrect citation, missing the closing '}'.


    Example:

    @article{haouari2020arcov19,
      title={ArCOV-19: The First Arabic COVID-19 Twitter Dataset with Propagation Networks},
      author={Fatima Haouari and Maram Hasanain and Reem Suwaileh and Tamer Elsayed},
      journal={arXiv preprint arXiv:2004.05861},
      year={2020}

    """
    ids_expected = {"bigIR/ar_cov19"}
    connector = HuggingFaceDatasetConnector()
    with responses.RequestsMock() as mocked_requests:
        path_data_list = (
            path_test_resources()
            / "connectors"
            / "huggingface"
            / "data_list_incorrect_citation.json"
        )
        with open(path_data_list, "r") as f:
            response = json.load(f)
        mocked_requests.add(
            responses.GET,
            "https://huggingface.co/api/datasets?full=True",
            json=response,
            status=200,
        )
        for dataset_id in ids_expected:
            mock_parquet(mocked_requests, dataset_id)
        resources_with_relations = list(connector.fetch())
    (related_resources,) = [r.related_resources for r in resources_with_relations]
    (citation,) = related_resources["citation"]
    assert citation.aiod_entry.status == "published"
    assert (
        citation.name == "ArCOV-19: The First Arabic COVID-19 Twitter Dataset with Propagation "
        "Networks"
    )
    assert citation.platform_resource_identifier == "haouari2020arcov19"
    assert citation.type == "article"
    assert (
        citation.description.plain == "By Fatima Haouari and Maram Hasanain and Reem Suwaileh "
        "and Tamer Elsayed"
    )


def mock_parquet(mocked_requests: responses.RequestsMock, dataset_id: str):
    filename = f"parquet_{dataset_id.replace('/', '_')}.json"
    path_split = path_test_resources() / "connectors" / "huggingface" / filename
    with open(path_split, "r") as f:
        response = json.load(f)
    status = 200 if "error" not in response else 404
    mocked_requests.add(
        responses.GET,
        f"{HUGGINGFACE_URL}/parquet?dataset={dataset_id}",
        json=response,
        status=status,
    )
