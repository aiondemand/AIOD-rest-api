#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from elasticsearch import Elasticsearch

# Global parameters
SIZE = 2
SORT = {"identifier": "asc"}

def main(index, search_concept, platforms):

    # Get elasticsearch password
    with open("../.env", "r") as f:
        for line in f:
            if "ES_PASSWORD" in line:
                elastic_password = line.split("=")[1][:-1]
            if "ES_USER" in line:
                elastic_user = line.split("=")[1][:-1]
    
    # Generate client
    es_client = Elasticsearch("http://localhost:9200",
                              basic_auth=(elastic_user, elastic_password))

    # Prepare query
    # -------------------------------------------------------------------------
    
    # Search fields corresponding to the indices
    match_fields = ['name', 'description']
    if ('dataset' in index) or ('publication' in index):
        match_fields.append('issn')
    if 'publication' in index:
        match_fields.append('isbn')
    if 'service' in index:
        match_fields.append('slogan')
    
    # Matches of the search concept for each field
    query_matches = [{'match': {f: search_concept}} for f in match_fields]
    
    if platforms:
        
        # Matches of the platform field for each selected platform
        platform_matches = [{'match': {'platform': p}} for p in platforms]
        
        # Query must match platform and search concept on at least one field
        query = {
            'bool': {
                'must': {
                    'bool': {
                        'should': platform_matches,
                        'minimum_should_match': 1
                    }
                },
                'should': query_matches,
                'minimum_should_match': 1
            }
        }
    
    else:
        
        # Query must match search concept on at least one field
        query = {
            'bool': {
                'should': query_matches,
                'minimum_should_match': 1
            }
        }
    
    # -------------------------------------------------------------------------
    
    # Perform first search
    result = es_client.search(index=index, query=query, size=SIZE, sort=SORT)

    # Print total number of results
    print(f"TOTAL RESULTS: {result['hits']['total']['value']}")

    query_result = 1
    while result["hits"]["hits"]:

        # Print current results
        print(f"QUERY RESULT: {query_result}")
        print(json.dumps(dict(result)["hits"]["hits"], indent=4))

        # Actualise search_after and query_result for the next search
        search_after = result["hits"]["hits"][-1]["sort"]
        query_result += 1

        # Perform next search
        result = es_client.search(
            index=index, query=query, size=SIZE, search_after=search_after, sort=SORT
        )


if __name__ == "__main__":
    index = ["publication"]  # List of assets
    search_concept = "in"  # Search concept
    platforms = ["example", "ai4experiments"]  # List of platforms
    main(index, search_concept, platforms)
