FROM python:3.11-slim-bullseye
# This comment should trigger Docker CI

# default-mysql-client is not necessary, but can be useful when debugging connection issues.
RUN apt-get update && apt-get -y install python3-dev default-libmysqlclient-dev build-essential \
    default-mysql-client pkg-config

WORKDIR /app

# Add ~/.local/bin to the PATH. Not necessary, but can be useful for debugging and bypasses pip
# warnings.
ENV PATH="${PATH}:/home/apprunner/.local/bin"


# Install python packages globally, so that it can also be used from cron dockers (running as root)
COPY ./pyproject.toml /app/pyproject.toml
RUN pip install .

# This can be overwritten by a live volume, to support live code changes
COPY ./src /app

# Create a non-root user for security
RUN groupadd -r apprunner && \
   useradd -mg apprunner apprunner \
   && chown -R apprunner:apprunner /app
USER apprunner:apprunner
