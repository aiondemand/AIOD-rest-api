# Getting Started
This page has information on how to host your own metadata catalogue.
If you plan to locally develop the REST API, please follow the installation procedure in ["Contributing"](../contributing.md)
after following the instructions on this page.

## Prerequisites
The platform is tested on Linux, but should also work on Windows and MacOS.
Additionally, it needs [Docker](https://docs.docker.com/get-docker/) and
[Docker Compose](https://docs.docker.com/compose/install/) (version 2.21.0 or higher).

## Installation
Starting the metadata catalogue is as simple as spinning up the docker containers through docker compose.
This means that other than the prerequisites, no installation steps are necessary.
However, we do need to fetch files from the latest release of the repository:

=== "CLI (git)"
    ```commandline
    git clone https://github.com/aiondemand/AIOD-rest-api.git
    ```

    It is also possible to clone using [SSH](https://docs.github.com/en/authentication/connecting-to-github-with-ssh).
    If you plan to develop the metadata catalogue, check the ["Contributing"](../contributing.md#cloning) page
    for more information on this step.

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
 * Metadata Catalogue REST API: The main API service for managing and accessing metadata.
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
--8<-- "./docs/hosting/connectors.md:4:30"

For more information, see the ["Connectors"](connectors.md) page.

## Configuration
There are two main places to configure the metadata catalogue services:
environment variables configured in `.env` files, and REST API configuration in a `.toml` file.
The default files are `./.env` and `./src/config.default.toml` shown below.

If you want to use non-default values, we strongly encourage you not to overwrite the contents of these files.
Instead, you can create `./override.env` and `./src/config.override.toml` files to override those files.
When using the `./scripts/up.sh` script to launch your services, these overrides are automatically taken into account.

=== "`./src/config/default.toml`"
    ```toml
    --8<-- "./src/config.default.toml"
    ```

=== "`./.env`"
    ```.env
    --8<-- ".env"
    ```

If you do not use `./scripts/up.sh` you can make sure the environment files are included by specifying them
in your `docker compose up` call, e.g.: `docker compose --env-file=.env --env-file=override.env up`.
Note that **order is important**, later environment files will override earlier ones.

Overwriting `.env` or `src/config.default.toml` directly will likely complicate updating to newer releases due to merge conflicts.

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

### Creating the Database

By default, the server will create a database on the provided MySQL server if it does not yet exist.
You can change this behavior through the **build-database** configuration parameter in `src/config.override.toml`,
it takes the following options:

* never: *never* creates the database, not even if there does not exist one yet.
  Use this only if you expect the database to be created through other means, such
  as MySQL group replication.
* if-absent: Creates a database only if none exists. (default)
* drop-then-build: Drops the database on startup to recreate it from scratch.
  **THIS REMOVES ALL DATA PERMANENTLY. NO RECOVERY POSSIBLE.**

### Populating the Database
To populate the database with some examples, run the `connectors/fill-examples.sh` script.
When using `docker compose` you can easily do this by running the "examples" profile:
`docker compose --profile examples up`
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

[//]: # (TODO: Write documentation for when some of the migrations are not applicable. E.g., when a table was created in a new release.)

#### Using connectors
You can start different connectors using their profiles, e.g.:

```bash
docker compose --profile examples --profile huggingface-datasets --profile openml --profile zenodo-datasets up -d
docker compose --profile examples --profile huggingface-datasets --profile openml --profile zenodo-datasets down
```

Make sure you use the same profile for `up` and `down`, or use `./scripts/down.sh` (see below),
otherwise some containers might keep running.

### Shorthands
We provide two auxiliary scripts for launching docker containers and bringing them down.
The first, `./scripts/up.sh` invokes `docker compose up -d` and takes any number of profiles to launch as parameters.
It will also ensure that the changes of the configurations (see above) are observed.
If `USE_LOCAL_DEV` is set to `true` (e.g., in `override.env`) then your local source code will be mounted on the containers,
this is useful for local development but should not be used in production.
E.g., with `USE_LOCAL_DEV` set to `true`, `./scripts/up.sh` resolves to:
`docker compose --env-file=.env --env-file=override.env -f docker-compose.yaml -f docker-compose.dev.yaml --profile examples  up -d`

The second script is a convenience for bringing down all services, including all profiles: `./scripts/down.sh`
