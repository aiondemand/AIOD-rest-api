import logging
import typing

import bibtexparser
import requests
from huggingface_hub import list_datasets
from huggingface_hub.hf_api import DatasetInfo

from connectors.abstract.resource_connector_on_start_up import ResourceConnectorOnStartUp
from connectors.record_error import RecordError
from connectors.resource_with_relations import ResourceWithRelations
from database.model import field_length
from database.model.agent.person import Person
from database.model.ai_asset.distribution import Distribution
from database.model.ai_resource.text import Text
from database.model.concept.aiod_entry import AIoDEntryCreate
from database.model.dataset.dataset import Dataset
from database.model.knowledge_asset.publication import Publication
from database.model.platform.platform_names import PlatformName
from database.model.resource_read_and_create import resource_create


class HuggingFaceDatasetConnector(ResourceConnectorOnStartUp[Dataset]):
    """
    This connector only runs on startup, because there is no endpoint to filter the huggingface
    data by last modified datetime
    """

    @property
    def resource_class(self) -> type[Dataset]:
        return Dataset

    @property
    def platform_name(self) -> PlatformName:
        return PlatformName.huggingface

    @staticmethod
    def _get(url: str, dataset_id: str) -> typing.List[typing.Dict[str, typing.Any]]:
        response = requests.get(url, params={"dataset": dataset_id})
        response_json = response.json()
        if not response.ok:
            msg = response_json["error"]
            logging.error(
                f"Error while fetching parquet info for dataset {dataset_id}: " f"'{msg}'"
            )
            return []
        return response_json["parquet_files"]

    def fetch(
        self, limit: int | None = None
    ) -> typing.Iterator[ResourceWithRelations[Dataset] | RecordError]:
        pydantic_class = resource_create(Dataset)
        pydantic_class_publication = resource_create(Publication)
        for dataset in list_datasets(full=True, limit=limit):
            try:
                yield self.fetch_dataset(dataset, pydantic_class, pydantic_class_publication)
            except Exception as e:
                yield RecordError(identifier=dataset.id, error=e)

    def fetch_dataset(self, dataset: DatasetInfo, pydantic_class, pydantic_class_publication):
        citations = []
        if hasattr(dataset, "citation") and dataset.citation:
            parsed_citations = bibtexparser.loads(dataset.citation).entries
            if len(parsed_citations) == 0:
                if dataset.citation:
                    citations = [
                        pydantic_class_publication(
                            name=dataset.citation,
                        )
                    ]
            else:
                citations = [
                    pydantic_class_publication(
                        platform=self.platform_name,
                        platform_resource_identifier=citation["ID"],
                        name=citation["title"],
                        same_as=citation["link"] if "link" in citation else None,
                        type=citation["ENTRYTYPE"],
                    )
                    for citation in parsed_citations
                ]

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
        if dataset.card_data is not None and "license" in dataset.card_data:
            if isinstance(dataset.card_data["license"], str):
                ds_license = dataset.card_data["license"]
            else:
                (ds_license,) = dataset.card_data["license"]

            # TODO(issue 8): implement
            # if "dataset_info" in dataset.cardData:
            #     size = sum(
            #         split["num_examples"]
            #         for split in dataset.cardData["dataset_info"]["splits"]
            #     )
        related_resources = {"citation": citations}
        if dataset.author is not None:
            related_resources["creator"] = [Person(name=dataset.author)]

        description = getattr(dataset, "description", None)
        if description and len(description) > field_length.LONG:
            text_break = " [...]"
            description = description[: field_length.LONG - len(text_break)] + text_break
        if description:
            description = Text(plain=description)

        return ResourceWithRelations[Dataset](
            resource=pydantic_class(
                aiod_entry=AIoDEntryCreate(status="published"),
                platform_resource_identifier=dataset.id,
                platform=self.platform_name,
                name=dataset.id,
                same_as=f"https://huggingface.co/datasets/{dataset.id}",
                description=description,
                date_published=dataset.createdAt if hasattr(dataset, "createdAt") else None,
                license=ds_license,
                distributions=distributions,
                is_accessible_for_free=True,
                size=size,
                keywords=dataset.tags,
            ),
            related_resources=related_resources,
        )
