# Hosting the Metadata Catalogue
This page has information on how to host your own metadata catalogue.
If you plan to locally develop the REST API, please follow the installation procedure in ["Contributing"](../contributing) instead.

## Prerequisites
The platform is tested on Linux, but should also work on Windows and MacOS.
Additionally, it needs [Docker](https://docs.docker.com/get-docker/) and 
[Docker Compose](https://docs.docker.com/compose/install/) (version 2.21.0 or higher).

## Installation
Starting the metadata catalogue is as simple as spinning up the docker containers through docker compose.
This means that other than the prerequisites, no installation steps are necessary.
However, we do need to fetch files the latest release of the repository:

=== "CLI (git)"
    ```commandline
    git clone https://github.com/aiondemand/AIOD-rest-api.git
    ```

=== "UI (browser)"
    
    * Navigate to the project page [aiondemand/AIOD-rest-api](https://github.com/aiondemand/AIOD-rest-api). 
    * Click the green `<> Code` button and download the `ZIP` file. 
    * Find the downloaded file on disk, and extract the content.

## Starting the Metadata Catalogue
From the root of the project directory (i.e., the directory with the `docker-compose.yaml` file), run:

=== "Shorthand"
    We provide the following script as a convenience.
    This is especially useful when running with a non-default or development configuration,
    more on that later.
    ```commandline
    ./scripts/up.sh
    ```
=== "Docker Compose"
    ```commandline
    docker compose up -d
    ```

This will start a number of services running within one docker network:

 * Database: a [MySQL](https://dev.mysql.com) database that contains the metadata.
 * Keycloak: an authentication service, provides login functionality.
 * Metadata Catalogue REST API: 
 * Elastic Search: indexes metadata catalogue data for faster keyword searches.
 * Logstash: Loads data into Elastic Search.
 * Deletion: Takes care of cleaning up deleted data.
 * nginx: Redirects network traffic within the docker network.
 * es_logstash_setup: Generates scripts for Logstash and creates Elastic Search indices.

[//]: # (TODO: Make list items link to dedicated pages.)
These services are described in more detail in their dedicated pages.
After the previous command was executed successfully, you can navigate to [localhost](http://localhost.com)
and see the REST API documentation. This should look similar to the [api.aiod.eu](https://api.aiod.eu) page,
but is connected to your local database and services.

### Starting Connector Services
To start connector services that automatically index data from external platforms into the metadata catalogue,
you must specify their docker-compose profiles (as defined in the `docker-compose.yaml` file).
For example, you can use the following commands when starting the connectors for OpenML and Zenodo.

=== "Shorthand"
    ```commandline
    ./scripts/up.sh openml zenodo-datasets
    ```
=== "Docker Compose"
    ```commandline
    docker compose --profile openml --profile zenodo-datasets up -d
    ```

The full list of connector profiles are:

- openml: indexes datasets and models from OpenML.
- zenodo-datasets: indexes datasets from Zenodo.
- huggingface-datasets: indexes datasets from Hugging Face.
- examples: fills the database with some example data. Do not use in production.

[//]: # (TODO: Link to docs or consolidate in dedicated page.)

## Configuration
There are two main places to configure the metadata catalogue services: 
environment variables configured in `.env` files, and REST API configuration in a `.toml` file.
The default files are `./.env` and `./src/config.default.toml` shown below.

If you want to use non-default values, we strongly encourage you not to overwrite the contents of these files.
Instead, you can create `./override.env` and `./config.override.toml` files to override those files.
When using the `./scripts/up.sh` script to launch your services, these overrides are automatically taken into account.

=== "`./src/config/default.toml`"
    ```toml
    --8<-- "./src/config.default.toml"
    ```

=== "`./.env`"
    ```.env
    --8<-- ".env"
    ```

Overwriting these files directly will likely complicate updating to newer releases due to merge conflicts.

## Updating to New Releases

[//]: # (TODO: Publish to docker hub and have the default docker-compose.yaml pull from docker hub instead.)

First, stop running services:
```commandline
./scripts/down.sh
```
Then get the new release:
```commandline
git fetch origin
git checkout vX.Y.Z
```
A new release might come with a database migration.
If that is the case, follow the instructions in ["Database Schema Migration"](#database-schema-migration) below.
The database schema migration must be performed before resuming operations.

Then run the startup commands again (either `up.sh` or `docker compose`).

### Database Schema Migration

We use [Alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html#running-our-first-migration) to automate database schema migrations
(e.g., adding a table, altering a column, and so on).
Please refer to the Alembic documentation for more information.
Commands below assume that the root directory of the project is your current working directory.

!!! warning

    Database migrations may be irreversible. Always make sure there is a backup of the old database.

Build the database schema migration docker image with:
```commandline
docker build -f alembic/Dockerfile . -t aiod-migration
```

With the sqlserver container running, you can migrate to the latest schema with

```commandline
docker run -v $(pwd)/alembic:/alembic:ro  -v $(pwd)/src:/app -it --network aiod-rest-api_default  aiod-migration
```

since the default entrypoint of the container specifies to upgrade the database to the latest schema.

Make sure that the specified `--network` is the docker network that has the `sqlserver` container.
The alembic directory is mounted to ensure the latest migrations are available,
the src directory is mounted so the migration scripts can use defined classes and variable from the project.

[//]: # (TODO: Write documentation for when some of the migrations are not applicable. E.g., when a database was created in a new release.)
