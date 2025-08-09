# Database Schema Migrations

We use [Alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html#running-our-first-migration) to automate database schema migrations
(e.g., adding a table, altering a column, and so on).
Put simply: it allows us to specify database schema migrations using Python in a structured manner.

This document outlines the general workflow of using Alembic for the Metadata Catalogue.
Examples of migration scripts can be found in the different schema subpages, e.g., ["Changing Attributes"](attributes.md).
For other general usage of Alembic, please refer to its documentation.

## Usage
We run alembic from a docker container, because it makes it convenient to connect to the docker network.
Commands below assume that the root directory of the project is your current working directory.

First, build the image with:
```commandline
docker build -f alembic/Dockerfile . -t aiod-migration
```

With the sqlserver container running (e.g., by using `./scripts/up.sh`, you can migrate to the latest schema with:

```commandline
docker run -v $(pwd)/alembic:/alembic:ro  -v $(pwd)/src:/app -it --network aiod-rest-api_default  aiod-migration
```
Make sure that the specified `--network` is the docker network that has the `sqlserver` container.
The alembic directory is mounted to ensure the latest migrations are available,
the src directory is mounted so the migration scripts can use defined classes and variable from the project.

## Update the Database

!!! warning "Database migrations may be irreversible!"
    Always make sure there is a backup of the old database.

Following the usage commands above, on a new release we should run Alembic to ensure the latest schema changes are applied.
The default entrypoint of the container specifies to upgrade the database to the latest schema.

### Updating the Database from Develop
During development, you will likely delete and recreate the database with some regularity.
It is inevitable that your database schema will then be created according to the current SQLModels defined in the metadata catalogue.
However, if you would attempt to run the Alembic migrations from scratch, they would no longer work since they assume a different initial schema.

Alembic stores information on the migration status in the database.
We can update the database entry to tell Alembic on which revision we are.
For example, to find out what revision `develop` is on:

1. Check out the development branch, and ensure there are no local changes (in `./alembic`).
2. Start docker compose, ensure the database is running, and start the alembic container with `--entrypoint=/bin/bash`.
2. Run `alembic head` to get the hash of the latest revision (e.g., `d09ed8ad4533`), or use `alembic history` to find the right hash.
3. Run `alembic stamp HASH` where `HASH` is replaced with the hash from the previous step.
4. If you're sure you just need the latest version, you can do `alembic stamp heads` directly.

## Adding a Revision

Build the docker image above, and start a container of it with shell as entry:

```bash
docker run -v $(pwd)/alembic:/alembic  -v $(pwd)/src:/app -it --network aiod-rest-api_default --entrypoint=/bin/bash  aiod-migration
```

Then follow regular `alembic` steps:
```bash
alembic revision -m "revision message"
```
Then edit the generated file (note that it should also exist on your host machine, so you might prefer to edit it there).

Note that working from a docker container is not strictly necessary, but it helps set up the PYTHONPATH correctly, so that you can import from the `src` directory.

## TODO
 - set up support for auto-generating migration scripts: https://alembic.sqlalchemy.org/en/latest/autogenerate.html
 - fix the dockerfile so the generated image can directly run alembic
