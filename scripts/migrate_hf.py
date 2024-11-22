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
import time

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
    logging.basicConfig(level=logging.INFO)
    AIoDConcept.metadata.create_all(EngineSingleton().engine, checkfirst=True)
    with DbSession() as session:
        datasets_query = select(Dataset).where(Dataset.platform == PlatformName.huggingface)
        datasets = session.scalars(datasets_query).all()

    logging.info(f"Found {len(datasets)} huggingface datasets.")
    is_old_style_identifier = lambda identifier: any(char not in string.hexdigits for char in identifier)
    datasets = [
        dataset for dataset in datasets
        if is_old_style_identifier(dataset.platform_resource_identifier)
    ]
    logging.info(f"Found {len(datasets)} huggingface datasets that need an update.")

    for i, dataset in enumerate(datasets):
        try:
            response = requests.get(
                f"https://huggingface.co/api/datasets/{dataset.name}",
                params={"full": "False"},
                headers={},
                timeout=10,
            )
        except Exception as e:
            logging.warning(f"Error retrieving dataset {dataset.name}: {e}")
            continue

        if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
            logging.info(
                f"Did not update dataset {dataset.name} as rate limit was exceeded."
                "Rerun the script at a later time to correct this dataset's identifier."
            )
            # I can't find information on the dataset API fetch rate limits, this is for safety.
            time.sleep(60)
            continue

        if response.status_code != HTTPStatus.OK:
            logging.warning(
                f"Dataset {dataset.name} could not be retrieved."
                "This is almost always an indication that the dataset is removed, "
                "so we are removing it from the index."
            )
            with DbSession() as session:
                session.delete(dataset)
            continue

        dataset_json = response.json()
        if dataset.platform_resource_identifier != dataset_json["id"]:
            logging.info(
                f"Dataset {dataset.platform_resource_identifier} moved to {dataset_json['id']}"
                "Deleting the old entry. The new entry either already exists or"
                "will be added on a later synchronization invocation."
            )
            with DbSession() as session:
                session.delete(dataset)
            continue

        persistent_id = dataset_json["_id"]
        logging.info(
            f"Setting platform id of {dataset.platform_resource_identifier} to {persistent_id}"
        )
        dataset.platform_resource_identifier = persistent_id
        with DbSession() as session:
            session.add(dataset)
            session.commit()

        if i % 1000 == 0:
            logging.info(f"Processed {i} of {len(datasets)} entries")


if __name__ == "__main__":
    main()
