import logging
import math
import typing

import bibtexparser
import requests
from huggingface_hub import list_datasets
from huggingface_hub.hf_api import DatasetInfo

from connectors.abstract.resource_connector_on_start_up import ResourceConnectorOnStartUp
from connectors.record_error import RecordError
from connectors.resource_with_relations import ResourceWithRelations
from database.model import field_length
from database.model.agent.contact import Contact
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
            logging.warning(f"Unable to retrieve parquet info for dataset '{dataset_id}': '{msg}'")
            return []
        return response_json["parquet_files"]

    def fetch(
        self, limit: int | None = None
    ) -> typing.Iterator[ResourceWithRelations[Dataset] | RecordError]:
        pydantic_class = resource_create(Dataset)
        pydantic_class_publication = resource_create(Publication)
        pydantic_class_contact = resource_create(Contact)

        for dataset in list_datasets(full=True, limit=limit):
            try:
                yield self.fetch_dataset(
                    dataset, pydantic_class, pydantic_class_publication, pydantic_class_contact
                )
            except Exception as e:
                yield RecordError(identifier=dataset.id, error=e)

    def fetch_dataset(
        self,
        dataset: DatasetInfo,
        pydantic_class,
        pydantic_class_publication,
        pydantic_class_contact,
    ):
        citations = self._parse_citations(dataset, pydantic_class_publication)

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
                content_size_kb=math.ceil(pq_file["size"] / 1000),
            )
            for pq_file in parquet_info
        ]

        ds_license = None
        if (
            dataset.card_data is not None
            and "license" in dataset.card_data
            and dataset.card_data["license"]
        ):
            if isinstance(dataset.card_data["license"], str):
                ds_license = dataset.card_data["license"]
            else:
                # There can be more than one license in HF, e.g., ['cc-by-sa-3.0', 'gfdl']. This
                # seems weird, what does it mean to have two different licenses? That's why we're
                # only saving the first.
                ds_license = dataset.card_data["license"][0]

            # TODO(issue 8): implement
            # if "dataset_info" in dataset.cardData:
            #     size = sum(
            #         split["num_examples"]
            #         for split in dataset.cardData["dataset_info"]["splits"]
            #     )
        related_resources = {"citation": citations}
        if dataset.author is not None:
            related_resources["creator"] = [pydantic_class_contact(name=dataset.author)]

        description = getattr(dataset, "description", None)
        if description and len(description) > field_length.MAX_TEXT:
            text_break = " [...]"
            description = description[: field_length.MAX_TEXT - len(text_break)] + text_break
        if description:
            description = Text(plain=description)

        return ResourceWithRelations[pydantic_class](  # type:ignore
            resource=pydantic_class(
                aiod_entry=AIoDEntryCreate(status="published"),
                platform_resource_identifier=dataset.id,
                platform=self.platform_name,
                name=dataset.id,
                same_as=f"https://huggingface.co/datasets/{dataset.id}",
                description=description,
                date_published=dataset.created_at if hasattr(dataset, "created_at") else None,
                license=ds_license,
                distribution=distributions,
                is_accessible_for_free=not dataset.private,
                keyword=dataset.tags,
            ),
            resource_ORM_class=Dataset,
            related_resources=related_resources,
        )

    def _parse_citations(self, dataset, pydantic_class_publication) -> list:
        """Best effort parsing of the citations. There are many"""
        raw_citation = getattr(dataset, "citation", None)
        if raw_citation is None:
            return []

        try:
            parsed_citations = bibtexparser.loads(raw_citation).entries
            if len(parsed_citations) == 0 and raw_citation.startswith("@"):
                # Ugly fix: many HF datasets have a wrong citation (see testcase)
                parsed_citations = bibtexparser.loads(raw_citation + "}").entries
            elif len(parsed_citations) == 0 and len(raw_citation) <= field_length.NORMAL:
                # Sometimes dataset.citation is not a bibtex field, but just the title of an article
                return [
                    pydantic_class_publication(
                        name=raw_citation, aiod_entry=AIoDEntryCreate(status="published")
                    )
                ]
            return [
                pydantic_class_publication(
                    # The platform and platform_resource_identifier should be None: this publication
                    # is not stored on HuggingFace (and not identifiable within HF using,
                    # for instance, citation["ID"])
                    name=citation["title"],
                    same_as=citation["link"] if "link" in citation else None,
                    type=citation["ENTRYTYPE"],
                    description=Text(plain=f"By {citation['author']}")
                    if "author" in citation
                    else None,
                    aiod_entry=AIoDEntryCreate(status="published"),
                )
                for citation in parsed_citations
            ]
        except Exception:
            return []
            # Probably an incorrect bibtex. There are many mistakes in the HF citations. E.g.,
            # @Inproceedings(Conference) instead of @inproceedings (note the capitals).
