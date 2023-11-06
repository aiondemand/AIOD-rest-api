FROM ai4eu_server

COPY cron /etc/cron.d/aiod
COPY delete_old.sh /opt/deletion/script/delete_old.sh
COPY entry.sh /opt/deletion/script/entry.sh

USER root
RUN apt -y install cron
RUN chmod +x /etc/cron.d/aiod /opt/deletion/script/delete_old.sh
RUN crontab /etc/cron.d/aiod

WORKDIR /app