FROM ai4eu_server

COPY cron /etc/cron.d/aiod
COPY datasets.sh /opt/connectors/script/datasets.sh
COPY entry.sh /opt/connectors/script/entry.sh

USER root
RUN apt -y install cron
RUN chmod +x /etc/cron.d/aiod /opt/connectors/script/datasets.sh
RUN crontab /etc/cron.d/aiod

WORKDIR /app