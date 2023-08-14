#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from elasticsearch import Elasticsearch

# Global parameters
ELASTIC_USER = "elastic"
SIZE = 2
SORT = {'identifier': 'asc'}

def main(index, search_concept, platforms):
    
    # Get elasticsearch password
    with open('../.env', 'r') as f:
        for line in f:
            if "ES_PASSWORD" in line:
                elastic_password = line.split('=')[1][:-1]
                break
    
    # Generate client
    es_client = Elasticsearch("http://localhost:9200",
                              basic_auth=(ELASTIC_USER, elastic_password))
    
    #Prepare query
    platform_identifiers = [{'match': {'platform_identifier': p}}
                            for p in platforms]
    query = {'bool': {'must': {'match': {'title': search_concept}},
                      'must': {'bool': {'should': platform_identifiers}}}}
    
    # Perform first search
    result = es_client.search(index=index, query=query, size=SIZE, sort=SORT)
    
    # Print total number of results
    print(f"TOTAL RESULTS: {result['hits']['total']['value']}")
    
    query_result = 1
    while result['hits']['hits']:
        
        # Print current results
        print(f"QUERY RESULT: {query_result}")
        print(json.dumps(dict(result)['hits']['hits'], indent=4))
        
        # Actualise search_after and query_result for the next search
        search_after = result['hits']['hits'][-1]['sort']
        query_result += 1
        
        # Perform next search
        result = es_client.search(index=index, query=query, size=SIZE,
                                  search_after=search_after, sort=SORT)

if __name__ == "__main__":
    index = ["publication"] # List of assets
    search_concept = "in" # Search concept
    platforms = ['2', '4', '9'] # List of platforms
    main(index, search_concept, platforms)
