"""
Updates the metadata of Hugging Face entries to use `_id` instead of `id` as platform identifier.

The `id` field (i.e., `username/datasetname`, e.g., `pgijsbers/titanic`) is subject to change when
a user changes their username or the dataset name. The `_id` field is persistent across these changes,
so can be used to avoid indexing the same dataset twice under a different platform identifier.

To be run once (around sometime Nov 2024), likely not needed after that. See also #385, 392.
"""
import logging
import os
import string
from http import HTTPStatus
import time
from pathlib import Path

from sqlalchemy import select
from database.session import DbSession, EngineSingleton
from database.model.dataset.dataset import Dataset
from database.model.platform.platform import Platform
from database.model.platform.platform_names import PlatformName
from database.model.concept.concept import AIoDConcept

# Magic import which triggers ORM setup
import database.setup

import requests
import json

import re
from http import HTTPStatus


def fetch_huggingface_metadata() -> list[dict]:
    next_url = "https://huggingface.co/api/datasets"
    datasets = []
    while next_url:
        logging.info(f"Counted {len(datasets)} so far.")
        if token := os.environ.get("HUGGINGFACE_TOKEN"):
            headers = {"Authorization": f"Bearer {token}"}
        else:
            headers = {}
        response = requests.get(
            next_url,
            params={"limit": 1000, "full": "False"},
            headers=headers,
            timeout=20,
        )
        if response.status_code != HTTPStatus.OK:
            logging.info("Stopping iteration", response.status_code, response.json())
            break

        datasets.extend(response.json())

        next_info = response.headers.get("Link", "")
        if next_url_match := re.search(r"<([^>]+)>", next_info):
            next_url = next_url_match.group()[1:-1]
        else:
            next_url = None
    return datasets


def load_id_map():
    HF_DATA_FILE = Path(__file__).parent / "hf_metadata.json"
    if HF_DATA_FILE.exists():
        logging.info(f"Loading HF data from {HF_DATA_FILE}.")
        with open(HF_DATA_FILE, "r") as fh:
            hf_data = json.load(fh)
    else:
        logging.info("Fetching HF data from Hugging Face.")
        hf_data = fetch_huggingface_metadata()
        with open(HF_DATA_FILE, "w") as fh:
            json.dump(hf_data, fh)
    id_map = {data["id"]: data["_id"] for data in hf_data}
    return id_map


def main():
    logging.basicConfig(level=logging.INFO)
    AIoDConcept.metadata.create_all(EngineSingleton().engine, checkfirst=True)
    id_map = load_id_map()

    with DbSession() as session:
        datasets_query = select(Dataset).where(Dataset.platform == PlatformName.huggingface)
        datasets = session.scalars(datasets_query).all()

    logging.info(f"Found {len(datasets)} huggingface datasets.")
    is_old_style_identifier = lambda identifier: any(
        char not in string.hexdigits for char in identifier
    )
    datasets = [
        dataset
        for dataset in datasets
        if is_old_style_identifier(dataset.platform_resource_identifier)
    ]
    logging.info(f"Found {len(datasets)} huggingface datasets that need an update.")

    with DbSession() as session:
        for dataset in datasets:
            if new_id := id_map.get(dataset.platform_resource_identifier):
                dataset.platform_resource_identifier = new_id
                session.add(dataset)
            else:
                session.delete(dataset)
        session.commit()
    logging.info("Done updating entries.")


if __name__ == "__main__":
    main()
