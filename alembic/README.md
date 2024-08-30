# Database Schema Migrations

We use [Alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html#running-our-first-migration) to automate database schema migrations
(e.g., adding a table, altering a column, and so on).
Please refer to the Alembic documentation for more information.

## Usage
Commands below assume that the directory containing this readme is your current working directory.

Build the image with:
```commandline
docker build -f Dockerfile . -t aiod-migration
```

With the sqlserver container running, you can migrate to the latest schema with:

```commandline
docker run -v $(pwd):/alembic:ro -it --network aiod_default  aiod-migration
```
Make sure that the specifid `--network` is the docker network that has the `sqlserver` container.

## TODO
 - set up support for auto-generating migration scripts: https://alembic.sqlalchemy.org/en/latest/autogenerate.html