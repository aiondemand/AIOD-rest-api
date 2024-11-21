"""
Updates the metadata of Hugging Face entries to use `_id` instead of `id` as platform identifier.

The `id` field (i.e., `username/datasetname`, e.g., `pgijsbers/titanic`) is subject to change when
a user changes their username or the dataset name. The `_id` field is persistent across these changes,
so can be used to avoid indexing the same dataset twice under a different platform identifier.

To be run once (around sometime Nov 2024), likely not needed after that. See also #385, 392.
"""
import logging
import string
from http import HTTPStatus

from sqlalchemy import select
from database.session import DbSession, EngineSingleton
from database.model.dataset.dataset import Dataset
from database.model.platform.platform import Platform
from database.model.platform.platform_names import PlatformName
from database.model.concept.concept import AIoDConcept

# Magic import which triggers ORM setup
import database.setup

import requests


def main():
    AIoDConcept.metadata.create_all(EngineSingleton().engine, checkfirst=True)
    with DbSession() as session:
        datasets_query = select(Dataset).where(Dataset.platform == PlatformName.huggingface)
        datasets = session.scalars(datasets_query).all()

        for dataset in datasets:
            if all(c in string.hexdigits for c in dataset.platform_resource_identifier):
                continue  # entry already updated to use new-style id

            response = requests.get(
                f"https://huggingface.co/api/datasets/{dataset.name}",
                params={"full": "False"},
                headers={},
                timeout=10,
            )
            if response.status_code != HTTPStatus.OK:
                logging.warning(f"Dataset {dataset.name} could not be retrieved.")
                continue

            dataset_json = response.json()
            if dataset.platform_resource_identifier != dataset_json["id"]:
                logging.info(
                    f"Dataset {dataset.platform_resource_identifier} moved to {dataset_json['id']}"
                    "Deleting the old entry. The new entry either already exists or"
                    "will be added on a later synchronization invocation."
                )
                session.delete(dataset)
                continue

            persistent_id = dataset_json["_id"]
            logging.info(
                f"Setting platform id of {dataset.platform_resource_identifier} to {persistent_id}"
            )
            dataset.platform_resource_identifier = persistent_id
        session.commit()


if __name__ == "__main__":
    main()
