curl -u elastic:${ES_PASSWORD} -X PUT elasticsearch:9200/publication?pretty -H 'Content-Type: application/json' -d @/publication.json
curl -u elastic:${ES_PASSWORD} -X PUT elasticsearch:9200/dataset?pretty -H 'Content-Type: application/json' -d @/dataset.json
