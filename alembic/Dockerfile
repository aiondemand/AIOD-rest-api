FROM python:3.11-slim-bullseye

# default-mysql-client is not necessary, but can be useful when debugging connection issues.
RUN apt-get update && apt-get -y install python3-dev default-libmysqlclient-dev build-essential \
    default-mysql-client pkg-config

RUN python -m pip install alembic mysqlclient
WORKDIR /alembic
ENTRYPOINT ["alembic", "upgrade", "head"]
