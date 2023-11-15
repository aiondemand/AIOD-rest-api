#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generates the elasticsearch indices

Launched by the es_logstash_setup container in the docker-compose file.
"""

import os
import copy
from elasticsearch import Elasticsearch

from routers.search_routers import router_list

BASE_MAPPING = {
    "mappings" : {
        "properties" : {
            "date_modified" : {
                "type" : "date"
            },
            "identifier" : {
                "type" : "long"
            },
            "name" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "plain" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "html" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            }
        }
    }
}

def add_field(base_mapping, field):
    new_mapping = copy.deepcopy(base_mapping)
    new_mapping["mappings"]["properties"][field] = {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
    return new_mapping

def generate_mapping(entity, fields):
    mapping = BASE_MAPPING
    for field in fields:
        mapping = add_field(mapping, field)
    return mapping

def main():
    
    # Generate client
    es_user = os.environ['ES_USER']
    es_password = os.environ['ES_PASSWORD']
    es_client = Elasticsearch("http://elasticsearch:9200",
                              basic_auth=(es_user, es_password))
    
    # Search for entities and their extra fields
    global_fields = set(['name', 'plain', 'html'])
    entities = {}
    for router in router_list:
        extra_fields = list(router.match_fields^global_fields)
        entities[router.es_index] = extra_fields
    
    # Add indices with mappings
    for entity, fields in entities.items():
        mapping = generate_mapping(entity, fields)
        es_client.indices.create(index=entity, body=mapping, ignore=400)

if __name__ == "__main__":
    main()
