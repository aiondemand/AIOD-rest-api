#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generates the elasticsearch indices

Launched by the es_logstash_setup container in the docker-compose file.
"""

import copy
import logging

from definitions import BASE_MAPPING
from routers.search_routers import router_list
from routers.search_routers.elasticsearch import ElasticsearchSingleton
from setup_logger import setup_logger


def generate_mapping(fields):
    mapping = copy.deepcopy(BASE_MAPPING)
    for field_name in fields:
        mapping["mappings"]["properties"][field_name] = {
            "type": "text",
            "fields": {"keyword": {"type": "keyword"}},
        }
    return mapping


def main():
    setup_logger()
    es_client = ElasticsearchSingleton().client
    entities = {
        router.es_index: list(router.extra_indexed_fields) for router in router_list
    }
    logging.info("Generating indices...")
    for es_index, fields in entities.items():
        mapping = generate_mapping(fields)

        # ignore 400 cause by IndexAlreadyExistsException when creating an index
        es_client.indices.create(index=es_index, body=mapping, ignore=400)
    logging.info("Generating indices completed.")


if __name__ == "__main__":
    main()
