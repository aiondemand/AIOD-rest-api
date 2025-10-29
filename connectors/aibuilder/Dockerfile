FROM aiod_metadata_catalogue

USER root
RUN apt-get update && apt -y install cron

COPY cron /etc/cron.d/aiod
COPY mlmodels.sh /opt/connectors/script/mlmodels.sh
COPY entry.sh /opt/connectors/script/entry.sh

RUN chmod +x /etc/cron.d/aiod /opt/connectors/script/mlmodels.sh
RUN crontab /etc/cron.d/aiod

WORKDIR /app
