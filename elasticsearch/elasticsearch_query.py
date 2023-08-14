#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from elasticsearch import Elasticsearch

ELASTIC_USER = "elastic"
QUERY = {'match': {'title': "exotic"}}

def main():
    
    # Get elasticsearch password
    with open('../.env', 'r') as f:
        for line in f:
            if "ELASTIC_PASSWORD" in line:
                ELASTIC_PASSWORD = line.split('=')[1][:-1]
                break
    
    # Generate client
    es_client = Elasticsearch("http://localhost:9200",
                              basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD))
    
    # Search
    result = es_client.search(index="publication", query=QUERY)
    print(result['hits']['hits'])

if __name__ == "__main__":
    main()
