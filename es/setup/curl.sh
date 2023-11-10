curl -u ${ES_USER}:${ES_PASSWORD} -X PUT elasticsearch:9200/dataset?pretty -H 'Content-Type: application/json' -d @/dataset.json
curl -u ${ES_USER}:${ES_PASSWORD} -X PUT elasticsearch:9200/event?pretty -H 'Content-Type: application/json' -d @/event.json
curl -u ${ES_USER}:${ES_PASSWORD} -X PUT elasticsearch:9200/experiment?pretty -H 'Content-Type: application/json' -d @/experiment.json
curl -u ${ES_USER}:${ES_PASSWORD} -X PUT elasticsearch:9200/ml_model?pretty -H 'Content-Type: application/json' -d @/ml_model.json
curl -u ${ES_USER}:${ES_PASSWORD} -X PUT elasticsearch:9200/news?pretty -H 'Content-Type: application/json' -d @/news.json
curl -u ${ES_USER}:${ES_PASSWORD} -X PUT elasticsearch:9200/organisation?pretty -H 'Content-Type: application/json' -d @/organisation.json
curl -u ${ES_USER}:${ES_PASSWORD} -X PUT elasticsearch:9200/project?pretty -H 'Content-Type: application/json' -d @/project.json
curl -u ${ES_USER}:${ES_PASSWORD} -X PUT elasticsearch:9200/publication?pretty -H 'Content-Type: application/json' -d @/publication.json
curl -u ${ES_USER}:${ES_PASSWORD} -X PUT elasticsearch:9200/service?pretty -H 'Content-Type: application/json' -d @/service.json
