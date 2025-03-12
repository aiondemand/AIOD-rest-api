FROM aiod_metadata_catalogue

COPY organisations.sh /opt/connectors/script/organisations.sh
COPY events.sh /opt/connectors/script/events.sh
COPY news.sh /opt/connectors/script/news.sh
COPY entry.sh /opt/connectors/script/entry.sh
COPY cron /etc/cron.d/aiod


USER root
RUN apt -y install cron

RUN chmod +x /opt/connectors/script/organisations.sh
RUN chmod +x /opt/connectors/script/events.sh
RUN chmod +x /opt/connectors/script/news.sh
RUN chmod +x /opt/connectors/script/entry.sh
RUN crontab /etc/cron.d/aiod

WORKDIR /app
