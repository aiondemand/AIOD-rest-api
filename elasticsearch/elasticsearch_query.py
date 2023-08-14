#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from elasticsearch import Elasticsearch

ELASTIC_USER = "elastic"

SIZE = 2
INDEX = "publication"
QUERY = {'match': {'platform': "example"}}
QUERY = {'match': {'title': "in"}}
SEARCH_AFTER = None
SORT = {'identifier': 'asc'}

def main():
    
    global SEARCH_AFTER
    
    # Get elasticsearch password
    with open('../.env', 'r') as f:
        for line in f:
            if "ES_PASSWORD" in line:
                ELASTIC_PASSWORD = line.split('=')[1][:-1]
                break
    
    # Generate client
    es_client = Elasticsearch("http://localhost:9200",
                              basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD))
    
    # Search
    result = es_client.search(index=INDEX, query=QUERY, size=SIZE,
                              search_after=SEARCH_AFTER, sort=SORT)
    
    # Print total number of results
    print(f"TOTAL RESULTS: {result['hits']['total']['value']}")
    
    query_result = 1
    while result['hits']['hits']:
        
        # Print current results
        print(f"QUERY RESULT: {query_result}")
        print(json.dumps(dict(result)['hits']['hits'], indent=4))
        
        # Actualise search_after for the next search
        SEARCH_AFTER = result['hits']['hits'][-1]['sort']
        query_result += 1
        
        # Search
        result = es_client.search(index=INDEX, query=QUERY, size=SIZE,
                                  search_after=SEARCH_AFTER, sort=SORT)

if __name__ == "__main__":
    main()



#ELASTIC_USER = "elastic"
#QUERY = {'bool': {'must': [{'match': {'title': "Advances"}},
#                           {'match': {'platform_identifier': "4"}}]}}
#
#def main():
#
#    # Get elasticsearch password
#    with open('../.env', 'r') as f:
#        for line in f:
#            if "ES_PASSWORD" in line:
#                ELASTIC_PASSWORD = line.split('=')[1][:-1]
#                break
#
#    # Generate client
#    es_client = Elasticsearch("http://localhost:9200",
#                              basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD))
#
#    # Search
#    result = es_client.search(index="publication", query=QUERY)
#    print(result['hits']['hits'])
#
#if __name__ == "__main__":
#    main()
