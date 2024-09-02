# Database Schema Migrations

We use [Alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html#running-our-first-migration) to automate database schema migrations
(e.g., adding a table, altering a column, and so on).
Please refer to the Alembic documentation for more information.

## Usage
Commands below assume that the directory containing this readme is your current working directory.

Build the image with:
```commandline
docker build -f alembic/Dockerfile . -t aiod-migration
```

With the sqlserver container running, you can migrate to the latest schema with:

```commandline
docker run -v $(pwd)/alembic:/alembic:ro  -v $(pwd)/src:/app -it --network aiod_default  aiod-migration
```
Make sure that the specifid `--network` is the docker network that has the `sqlserver` container.
The alembic directory is mounted to ensure the latest migrations are available, 
the src directory is mounted so the migration scripts can use defined classes and variable from the project.

## Update the Database
> [!Caution]
> Database migrations may be irreversible. Always make sure there is a backup of the old database.

Following the usage commands above, on a new release we should run alembic to ensure the latest schema changes are applied.
The default entrypoint of the container specifies to upgrade the database to the latest schema.

## TODO
 - set up support for auto-generating migration scripts: https://alembic.sqlalchemy.org/en/latest/autogenerate.html
