FROM ubuntu:22.04

RUN apt-get update && apt-get install -y curl

COPY dataset.json /dataset.json
COPY event.json /event.json
COPY experiment.json /experiment.json
COPY ml_model.json /ml_model.json
COPY news.json /news.json
COPY organisation.json /organisation.json
COPY project.json /project.json
COPY publication.json /publication.json
COPY service.json /service.json
COPY create_indices.sh /create_indices.sh

ENTRYPOINT ["/bin/bash", "/create_indices.sh"]

