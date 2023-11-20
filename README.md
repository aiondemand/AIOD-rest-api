# AIoD API 

This repository contains the AI on Demand (AIoD) REST API. It is built with 
[FastAPI](https://fastapi.tiangolo.com/)
that interacts with a database ([MySQL](https://hub.docker.com/_/mysql))
and [OpenML's REST API](https://www.openml.org/apis).
Both the database and the REST API are run from docker in separate containers.

The AIoD REST API will allow any kind of service to interact with the AIoD portal to discover, 
retrieve, and share AI resources. It forms the connection between user-facing components, such 
as the AIoD website or Python Client API, and the backend. The metadata for datasets, models 
and other resources can be accessed, added, updated and deleted through this API. 

## Architecture
All metadata is stored in the AIoD metadata database. For every instance of the API (there will 
be multiple running instances, for reliability and performance), an instance of this database 
will run on the same machine (on the same node). The type of database is not yet determined, for 
now we use a simple MySQL database.

The metadata is stored in AIoD format. When the user requests an item, such as a dataset, it can 
be returned in AIoD format, or converted to any supported format, as requested by the user. For 
datasets, we will for instance support schema.org and DCAT-AP.

Requesting a dataset will therefore be simply:

![Get dataset UML](media/GetDatasetUML.png)

To fill the database, a synchronization process must be running continuously for every platform 
(e.g. HuggingFace or OpenML). This synchronization service of a platform will be deployed at a 
single node. The synchronization service queries its platform for updates, converts the metadata 
to the AIoD format and updates the database.

Note that this synchronization process between the platform and the database, is different from 
the synchronization between database instances. The latter is under discussion in the AIoD 
Synchronization Meetings. 

### AIoD Metadata

The models are found in `src/database/model`. The AIoD Metadata team is responsible for 
determining the fields of the metadata, whereafter the classes are implemented in this metadata 
catalogue. To check the existing fields, the easiest way it to start this application (see 
"Using Docker Compose") and check the automatically generated swagger documentation 
(http://localhost:8000/docs).

We use inheritance to make sure that generic fields, such as name and description, are present 
and consistent over all resources. A partial overview of the metadata model can be found in the 
following figure:

![AIoD Metadata model](media/AIoD_Metadata_Model.drawio.png)

## Prerequisites
- Linux/MacOS/Windows (should all work)
- [Docker](https://docs.docker.com/get-docker/) 
- [Docker Compose](https://docs.docker.com/compose/install/) version 2.21.0 or higher

For development:
- `Python3.11` with `python3.11-dev` (`sudo apt install python3.11-dev` on Debian)
- Additional 'mysqlclient' dependencies. Please have a look at [their installation instructions]
  (https://github.com/PyMySQL/mysqlclient#install).

## Production environment

For production environments elasticsearch recomends -Xss4G and -Xmx8G for the JVM settings.\
This parameters can be defined in the .env file.
See the [elasticsearch guide](https://www.elastic.co/guide/en/logstash/current/jvm-settings.html).

## Installation

This repository contains two systems; the database and the REST API.
As a database we use a containerized MySQL server (through Docker), the REST API can be run locally or containerized.
Information on how to install Docker is found in [their documentation](https://docs.docker.com/desktop/).

### Using docker compose
```bash
docker compose --profile examples up
```

starts the MYSQL Server, the REST API, Keycloak for Identy and access management and Nginx for reverse proxing. \
Once started, you should be able to visit the REST API server at: http://localhost and Keycloak at http://localhost/aiod-auth \
To authenticate to the REST API swagger interface the predefined user is: user, and password: password \
To authenticate as admin to Keycloak the predefined user is: admin and password: password \
To use a different DNS hostname replace localhost with it in .env and src/config.toml \
This configuration is intended for development, DO NOT use it in production. 

To turn if off again, use 
```bash
docker compose --profile examples down
```

To connect to the database use `./scripts/database-connect.sql`.

```bash
mysql> SHOW DATABASES;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| performance_schema |
| sys                |
+--------------------+
4 rows in set (0.03 sec)
```

Now, you can visit the server from your browser at `localhost:8000/docs`.

#### Using connectors
You can specify different connectors using

```bash
docker compose --profile examples --profile huggingface-datasets --profile openml-datasets up -d
docker compose --profile examples --profile huggingface-datasets --profile openml-datasets down
```

Make sure you use the same profile for `up` and `down`, otherwise some containers might keep 
running.

#### Local Installation

If you want to run the server locally, you need **Python 3.11**.
We advise creating a virtual environment first and install the dependencies there:

```bash
python3.11 -m venv venv
source venv/bin/activate
python -m pip install .
```

For development, you will need to install the optional dependencies as well:

```bash
source venv/bin/activate
python -m pip install ".[dev]"
```

Moreover, you are encouraged to install the pre-commit hooks, so that black, mypy and the unittests
run before every commit:
```bash
pre-commit install
```
You can run 
```bash
pre-commit run --all-files
```
To run pre-commit manually.

After installing the dependencies you can start the server. You have 3 options:

1. Run from your machine: 
```bash
cd src
python main.py --reload
```
The `--reload` argument will automatically restart the app if changes are made to the source files.
2. Run using docker. For instance using `scripts/run_apiserver.sh`
3. Run using DevContainer (see next subsection)

### Authentication
Currently, the code is by default running using the local Keycloak. To make 
this work, you need to set an environment variable. You can do this by setting the 
`KEYCLOAK_CLIENT_SECRET` in `src/.env`.

```bash
# src/.env
KEYCLOAK_CLIENT_SECRET=[SECRET]
```

Alternatively, you can connect to a different keycloak instance by modifying `src/.env`. EGI 
Checkin can for instance be used on a deployed instance - not on local host. Marco Rorro is the 
go-to person to request the usage of the EGI Checkin.

The reason that EGI Checkin doesn't work on localhost, is that the redirection url of EGI 
Checkin is strict - as it should be. On our development keycloak, any redirection url is 
accepted, so that it works on local host or wherever you deploy. This should never be the case 
for a production instance.

See [authentication README](authentication/README.md) for more information.

### Populating the Database

By default, the app will connect to the database and populate it with a few items if there is no data present.
You can change this behavior through parameters of the script:

* **rebuild-db**: "no", "only-if-empty", "always". Default is "data".
    * no: connect to the database but don't make any modifications on startup.
    * only-if-empty: if the database does not exist, create it. Then, if the tables do not exist, create them.
      Then, if the tables are empty, populate according to `populate`.
    * always: drop the configured database and rebuild its structure from scratch.
      Effectively a `DROP DATABASE` followed by a `CREATE DATABASE` and the creation of the tables.
      The database is then repopulated according to `populate`.
      **Important:** data in the database is not restored. All data will be lost. Do not use this option
      if you are not sure if it is what you need.

* **populate-datasets**: one or multiple of "example", "huggingface", "zenodo" or "openml". 
  Default is nothing. Specifies what data to add the database, only used if `rebuild-db` is 
  "only-if-empty" or "always".
    * nothing: don't add any data.
    * example: registers two datasets and two publications.
    * openml: registers datasets of OpenML, this may take a while, depending on the limit (~30 
      minutes).

* **populate-publications**: similar to populate-datasets. Only "example" is currently implemented.

* **limit**: limit the number of initial resources with which the database is populated. This 
  limit is per resource and per platform.

## Usage

Following the installation instructions above, the server may be reached at `127.0.0.1:8000`.
REST API documentation is automatically built and can be viewed at `127.0.0.1:8000/docs`.


#### Automatically Restart on Change

If you want to automatically restart the server when a change is made to a file in the project, use the `--reload`
parameter.
It is important to realize that this also re-initializes the connection to the database, and possibly will do any
start-up work (e.g., populating the database).

#### Database Structure

The Python classes that define the database tables are found in [src/database/model/](src/database/model/). 
The structure is based on the 
[metadata schema](https://docs.google.com/spreadsheets/d/1n2DdSmzyljvTFzQzTLMAmuo3IVNx8yposdPLItBta68/edit?usp=sharing).


## Adding resources

See [src/README.md](src/README.md).

## Releases

### Breaking changes
Breaking changes of a resource include deleting a field, changing the name of an existing field, 
or changing the datatype of a field. Adding new fields is not a breaking change.

On a breaking change for a resource (e.g. for Dataset), a new router with a new version should 
be created. The existing router should be deprecated, and rewritten so that it can handle the 
new metadata of the database. This deprecation of a router will be visible in the Swagger 
documentation. Calls to a deprecated router will still work, but a response header "Deprecated" 
will be added with the deprecation date. The deprecated router will then be deleted on the next 
release.

On non-breaking changes of a resource, a new version is not needed for the corresponding router.

Example:
- Start www.aiod.eu/api/datasets/v0
- Release 1: www.aiod.eu/api/datasets/v0 (no breaking changes)
- Release 2:
  - www.aiod.eu/api/datasets/v0 (deprecated)
  - www.aiod.eu/api/datasets/v1
- Release 3: www.aiod.eu/api/datasets/v1

### Database migration

The database should always be up-to-date with the latest version of the metadata. As database 
migration tool, [Alembic](https://alembic.sqlalchemy.org/en/latest/) is the default choice for
SQLAlchemy. The setup of this db migration for AIOD remains a TODO for now. 

### Changelog

As changelog we use the Github tags. For each release, a release branch should be created with a 
bumped version in the pyproject.toml, and merged with the master. The tag should contain a 
message detailing all the breaking and non-breaking changes. This message should adhere to the 
guiding principles as described in https://keepachangelog.com/. 

- Show all tags: https://github.com/aiondemand/AIOD-rest-api/tags
- Show a specific tag: https://github.com/aiondemand/AIOD-rest-api/releases/tag/0.3.20220501

This information can also be extracted using the Github REST API.
