curl -u elastic:${ES_PASSWORD} -X PUT elasticsearch:9200/dataset?pretty -H 'Content-Type: application/json' -d @/dataset.json
curl -u elastic:${ES_PASSWORD} -X PUT elasticsearch:9200/experiment?pretty -H 'Content-Type: application/json' -d @/experiment.json
curl -u elastic:${ES_PASSWORD} -X PUT elasticsearch:9200/ml_model?pretty -H 'Content-Type: application/json' -d @/ml_model.json
curl -u elastic:${ES_PASSWORD} -X PUT elasticsearch:9200/publication?pretty -H 'Content-Type: application/json' -d @/publication.json
curl -u elastic:${ES_PASSWORD} -X PUT elasticsearch:9200/service?pretty -H 'Content-Type: application/json' -d @/service.json
