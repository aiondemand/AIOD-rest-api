import itertools
import logging
import typing

import bibtexparser
import datasets
import dateutil.parser
import requests

from connectors import ResourceConnector
from connectors.resource_with_relations import ResourceWithRelations
from database.model.ai_asset.distribution import Distribution
from database.model.dataset.dataset import Dataset
from database.model.knowledge_asset.publication import Publication
from database.model.platform.platform_names import PlatformName
from database.model.resource_read_and_create import resource_create


class HuggingFaceDatasetConnector(ResourceConnector[Dataset]):
    @property
    def resource_class(self) -> type[Dataset]:
        return Dataset

    @property
    def platform_name(self) -> PlatformName:
        return PlatformName.huggingface

    @staticmethod
    def _get(url: str, dataset_id: str) -> typing.List[typing.Dict[str, typing.Any]]:
        """
        Perform a GET request and raise an exception if the response code is not OK.
        """
        response = requests.get(url, params={"dataset": dataset_id})
        response_json = response.json()
        if not response.ok:
            msg = response_json["error"]
            logging.error(
                f"Error while fetching parquet info for dataset {dataset_id}: " f"'{msg}'"
            )
            return []
        return response_json["parquet_files"]

    def fetch_all(
        self, limit: int | None = None
    ) -> typing.Iterator[ResourceWithRelations[Dataset]]:
        pydantic_class = resource_create(Dataset)
        pydantic_class_publication = resource_create(Publication)
        for dataset in itertools.islice(datasets.list_datasets(with_details=True), limit):
            try:
                citations = []
                if dataset.citation is not None:
                    parsed_citations = bibtexparser.loads(dataset.citation).entries
                    if len(parsed_citations) == 0:
                        citations = [
                            pydantic_class_publication(
                                title=dataset.citation,
                                platform=self.platform_name,
                                platform_identifier=dataset.citation,
                                datasets=[],
                            )
                        ]
                    elif len(parsed_citations) == 1:
                        citation = parsed_citations[0]
                        citations = [
                            pydantic_class_publication(
                                title=citation["title"],
                                platform=self.platform_name,
                                platform_identifier=citation["ID"],
                                url=citation["link"] if "link" in citation else None,
                                datasets=[],
                            )
                        ]
                    else:
                        raise ValueError(
                            f"Unexpected number of citations found for dataset "
                            f"{dataset.id} in {dataset.citation}: {len(parsed_citations)}"
                        )

                parquet_info = HuggingFaceDatasetConnector._get(
                    url="https://datasets-server.huggingface.co/parquet",
                    dataset_id=dataset.id,
                )
                distributions = [
                    Distribution(
                        name=pq_file["filename"],
                        description=f"{pq_file['dataset']}. Config: {pq_file['config']}. Split: "
                        f"{pq_file['split']}",
                        content_url=pq_file["url"],
                        content_size_kb=pq_file["size"],
                    )
                    for pq_file in parquet_info
                ]
                size = None
                ds_license = None
                if dataset.cardData is not None:
                    if isinstance(dataset.cardData["license"], str):
                        ds_license = dataset.cardData["license"]
                    else:
                        (ds_license,) = dataset.cardData["license"]

                    # TODO(issue 8): implement
                    # if "dataset_info" in dataset.cardData:
                    #     size = sum(
                    #         split["num_examples"]
                    #         for split in dataset.cardData["dataset_info"]["splits"]
                    #     )
                yield ResourceWithRelations[Dataset](
                    resource=pydantic_class(
                        description=dataset.description,
                        name=dataset.id,
                        platform_identifier=dataset.id,
                        platform=self.platform_name,
                        same_as=f"https://huggingface.co/datasets/{dataset.id}",
                        creator=dataset.author,
                        date_modified=dateutil.parser.parse(dataset.lastModified),
                        license=ds_license,
                        distributions=distributions,
                        is_accessible_for_free=True,
                        size=size,
                        keywords=dataset.tags,
                        alternate_names=[],
                        citations=[],
                        is_part=[],
                        has_parts=[],
                        measured_values=[],
                    ),
                    related_resources={"citations": citations},
                )
            except Exception as e:
                logging.error(
                    f"Error while fetching huggingface dataset with id {dataset.id}: " f"{str(e)}"
                )
