# The AI-on-Demand Metadata Schema
The conceptual AI-on-Demand metadata schema is defined in its own dedicated repository [aiondemand/metadata-schema](https://github.com/aiondemand/metadata-schema).
Questions about the conceptual metadata schema and requests for changes should be directed at that repository instead.

In the REST API, we have an implementation of the schema defined in our [`src/database/model`](https://github.com/aiondemand/AIOD-rest-api/tree/develop/src/database/model) directory.
For the model implementation we make use of [SQLModel](https://sqlmodel.tiangolo.com/), a layer
on top of the ORM framework [SQLAlchemy](https://www.sqlalchemy.org/) and the serialization,
validation and documentation (creating Swagger) framework [pydantic](https://docs.pydantic.dev/),
created by the developer of FastAPI, the framework we use for routing.

SQLModel makes it possible to define only a single model instead of defining the database-layer
(SQLAlchemy) and the logic-layer (Pydantic) separately.
Our implementation relies on inheritance to follow the same class hierarchy as defined in the [metadata schema](https://github.com/aiondemand/metadata-schema),
this makes sure that generic fields, such as name and description, are present and consistent over all resources,
and changes to the conceptual model and the model implementation should be similar.

A partial overview of the metadata model can be found in the
following figure:

![AIoD Metadata model](../../media/AIoD_Metadata_Model.drawio.png)

In addition to the implementation of the metadata schema, we maintain some metadata about that metadata.
Specifically, a system which stores users, permissions, and reviews that relate to the metadata assets uploaded to AIoD.
More on this can be found in the ["User Model"](../users.md) documentation.

## Reading the Conceptual Metadata Schema
Tools and documentation on how to read the conceptual metadata model are currently being written.
This section will be updated at a later date (as of 16-12-2024).

## Reading the Metadata Schema Implementation
The metadata schema implementation is a hierarchy of classes that ultimately derive from `SQLModel`,
and mimic the hierarchy defined in the conceptual model.
However, we generally use multiple models of the same data to facilitate the differences between
what is stored in the database, and what is served to the user (or, alternatively, what the user
is supposed to provide through the API). This idea is also explained in SQLModel's
["multiple models with FastAPI"](https://sqlmodel.tiangolo.com/tutorial/fastapi/multiple-models/)
tutorial.

In general, you will see different classes of the forms `XBase`, `XORM`, `XCreate`.
The `XBase` class (where X is an entity, e.g., Dataset) provides attributes which are commonly used in all models:
they are used by the database, they define the fields available when uploading the asset,
and they are also returned to the user when they request the entity.

Derived from this `XBase` class are the `X` class, that defines the table and database specific attributes,
and `XRead` class, which defines the response model, though that is generated dynamically.

The `XORM` classes are for separate tables which do not directly represent concepts of the metadata catalogue.
Instead, they represent base classes in the class hierarchy, and facilitate resolving a parent-class identifier,
e.g., an Agent identifier, to its child class, e.g., a Person.

For more information on defining new objects in the conceptual model, see the ["objects"](objects.md) page.
For a brief discussion on how to read an attribute definition, see ["attributes"](attributes.md).
For a brief discussion on how to define relationships, see ["relationships"](relationships.md).

## Changing the Metadata Schema Implementation
On a high level, changes to the metadata schema implementation consist of three steps:

 * updating the schema implementation in [`src/database/model`](https://github.com/aiondemand/AIOD-rest-api/tree/develop/src/database/model),
 * updating or adding tests which test those changes, and
 * adding a [database migration script](migration.md) which updates the database accordingly.

This last step isn't needed during development, where you may recreate a database anytime to model changes.
However, to deploy the changed schema in production we need to be able to change the database,
both its schema and its content, to match the schema defined by the Python classes.
For this reason, a migration script is also _required_ when making changes to the metadata schema implementation.

The subsections in the sidebar document how to execute these steps depending on the type of change you want to make (work in progress):

 - [Attributes](attributes.md) explains how to work with attributes that do not refer to any external tables. For example, adding a field which stores a URL.
 - [Relationships](relationships.md) explains how to work with attributes which define relationships between objects. For example, an asset's creator which is represented with a link to an `Agent`.
 - [Objects](objects.md) explains how work with objects as a whole. For example, adding an entirely new entity to the schema.

## Tips For Making Migrations
The migration you write should work on a populated database from the `develop` branch.
The easiest way to easily reconstruct a database in that state quickly while iterating over the migration script, is to first create a back up:
```bash
git checkout develop
./scripts/down.sh
./scripts/clean.sh
./scripts/up.sh examples
```
Then wait for the examples to be populated (the fill-db-with-examples container should have stopped).
Next, figure out which revision your migration builds on (the `down_revision` in the script).
We can then make sure Alembic is aware the generated database schema mimics that revision:
```bash
# from the alembic docker container
alembic stamp <down_revision>
```
Now we have a database state we want to restore easily, so we create a back up:
```bash
# back in our own console
./scripts/mysql_dump.sh
```
you can now checkout your branch (`git checkout <branch>`) and test the migration.
It's now easy to restore state with the backup:
```bash
docker exec -it sqlserver mysql -uroot -pok -e "drop database aiod; create database aiod;"; ./scripts/mysql_restore.sh
```
and run the migration script as normal.

#### A Note on Identifiers
This note describes a change made around May 2025, and explains why objects have so many different identifiers that are all the same.

To represent inheritance in the database, auxiliary tables were introduced to provide unique identifiers at the parent level.
For example, every AI Resource has a unique identifier.
This allows for assets to specify relationships to AI Resources at a database level (as opposed to a union of all its subclasses).

???- "An example of the resulting tables"

    `ai_resource` table

    | identifier | type       |
    |------------|------------|
    | 1          | case study |
    | 2          | dataset    |
    | 3          | person     |

    `agent` table

    | identifier | type         |
    |------------|--------------|
    | 1          | organisation |
    | 2          | person       |

    `person` table

    | identifier | agent_id | ai_resource_id | aiod_entry_identifier | ... |
    |------------|----------|----------------|-----------------------|-----|
    | 1          | 2        | 3              | 4                     | ... |


These identifiers were all generated independently, which meant that one single asset could have many different identifiers.
For example, a Person which is an Agent, AIResource, and AIoDConcept, would have an `agent_id`, `ai_resource_id`, and `identifier`.
Depending on the relationship, a different one would have to be used, and they had different values.
This made it easy to unintentionally reference the wrong object, e.g., making "agent 1" a member of an organisation,
where "person 1" was meant instead (agent 1 can be a different person or organisation, as in the example!).

To avoid these kind of issues going forward, we created triggers which sync all these identifiers to be identical to the asset's `aiod_entry_identifier`.
This is because _all_ assets have an `aiod_entry_identifier`, and this identifier is guaranteed to be unique (since they originate from the same primary key column).
There are currently no plans to remove these additional identifiers in the back-end, but they may be hidden from users in the future.
If the different identifiers were to be merged into one, we would need to still be able to somehow guarantee validity of the relationships.
For example, this mechanism currently enforces that an Organisation's `members` attribute can only be populated with Agents and not e.g., Datasets.
