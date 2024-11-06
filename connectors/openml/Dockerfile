FROM aiod_metadata_catalogue

COPY cron /etc/cron.d/aiod
COPY datasets.sh /opt/connectors/script/datasets.sh
COPY mlmodels.sh /opt/connectors/script/mlmodels.sh
COPY entry.sh /opt/connectors/script/entry.sh

USER root
RUN apt -y install cron
RUN chmod +x /etc/cron.d/aiod /opt/connectors/script/datasets.sh
RUN chmod +x /etc/cron.d/aiod /opt/connectors/script/mlmodels.sh
RUN crontab /etc/cron.d/aiod

WORKDIR /app