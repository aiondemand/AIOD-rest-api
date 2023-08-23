# AIoD API - adding a resource 

This document describes the steps to perform to add a resource. 

## Model definition

First we need to know what the model will look like. For the core AIoD API, we make use of a 
spreadsheet with the name, type, cardinality, source (e.g. schema.org/Thing) and description of 
each field. Many resources inherit from AIAsset, containing fields such as `name`, `description` 
etc.

## Model implementation

### Background
For the model implementation we make use of [SQLModel](https://sqlmodel.tiangolo.com/), a layer 
on top of the ORM framework [SQLAlchemy](https://www.sqlalchemy.org/) and the serialization, 
validation and documentation (creating Swagger) framework [pydantic](https://docs.pydantic.dev/), 
created by the developer of FASTApi, the framework we use for routing.

SQLModel makes it possible to define only a single model instead of defining the database-layer 
(SQLAlchemy) and the logic-layer (Pydantic) separately.

We do want some separate model though, as described in 
[SQLModel multiple models](https://sqlmodel.tiangolo.com/tutorial/fastapi/multiple-models/). We 
might want to store an `ExampleEnum` in a separate table, to keep track of the possible values. 
But the user should not be distracted by this: in Swagger, it should just show as a string value,
not as a link to a separate table.

We created some additional functionality for this, to minimize the work of creating new classes 
with dependencies. 

### Steps

Let's start by creating a model in `src/database/model`. Let's call our example model 
Example. Create a separate directory with a new python file:
`src/database/model/example/example.py`.  In it we start with a `ExampleBase`, in which we put 
the fields that are not dependant on a separate table:


```python
from sqlmodel import Field
from database.model.resource_read_and_create import Resource

class ExampleBase(Resource):
    # Required fields
    unique_field: str = Field(max_length=150, unique=True,
                              schema_extra={"example": "Used for Swagger documentation."})
    string_field: str = Field(max_length=5000, schema_extra={"example": "A description."})
    # Recommended fields
    int_field: int | None = Field(default=None, schema_extra={"example": 22})
```

We probably need some separate tables as well. For instance for "enum" types: where we store the  
possible string values in a separate table. We put these in separate file, either 
`src/database/model/example/example_enum.py` or, if it's used by multiple models, in  
`src/database/model/general/example_enum.py`:

```python
from typing import List
from sqlmodel import Relationship
from typing import TYPE_CHECKING

from database.model.named_relation import NamedRelation

if TYPE_CHECKING:  # avoid circular imports; only import while type checking
    from database.model.example import Example


class ExampleEnum(NamedRelation, table=True):  # type: ignore [call-arg]
    """An example of an enum stored in a separate table"""

    __tablename__ = "example_enum"  # singular, so not "example_enums"

    examples: List["Example"] = Relationship(back_populates="license")
```

Next we create the `Example` in `src/database/model/example/example.py`, inheriting from 
`ExampleBase`.

```python
from sqlalchemy import UniqueConstraint
from database.model.relationships import ResourceRelationshipSingle
from sqlmodel import Field, Relationship
from database.model.serializers import (
    AttributeSerializer,
    FindByNameDeserializer
)


class Example(ExampleBase, table=True):  # type: ignore [call-arg]
    __tablename__ = "example"

    identifier: int = Field(primary_key=True, foreign_key="ai_asset.identifier")

    example_enum_identifier: int | None = Field(foreign_key="example_enum.identifier")
    example_enum: ExampleEnum | None = Relationship(back_populates="examples")

    class RelationshipConfig:  # This is AIoD-specific code, used to go from Pydantic to SqlAlchemy
        example_enum: str | None = ResourceRelationshipSingle(
            identifier_name="example_enum_identifier",
            serializer=AttributeSerializer("name"),  # code to serialize ORM to Pydantic
            deserializer=FindByNameDeserializer(ExampleEnum),  # deserialize Pydantic to ORM
            example="An example string value",
        )
```

### Types of relations
#### Many-to-one Enum
See `ExampleEnum` above. Example: `Dataset.license`: we keep a list of possible licenses. Each 
license relates back to multiple datasets.

#### Many-to-many Enum or one-to-many.
If, instead, we needed a many-to-many or one-to-many enum, we need a separate table linking them 
together. Example: `Dataset.alternate_name`:

In `src/database/model/example/example_enum.py`:
```python
from typing import TYPE_CHECKING

from sqlmodel import SQLModel, Field

if TYPE_CHECKING:  # avoid circular imports; only import while type checking
    from database.model.example import Example

class ExampleEnumLink(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "example_example_enum_link"

    example_identifier: int = Field(foreign_key="example.identifier", primary_key=True)
    example_enum_identifier: int = Field(foreign_key="example_enum.identifier", primary_key=True)
```

In `src/database/model/example/example.py`:
```python
class Example(ExampleBase, table=True):  # type: ignore [call-arg]
    # [...]
    example_enums: List[ExampleEnum] = Relationship(
        back_populates="examples", link_model=ExampleEnumLink
    )

    class RelationshipConfig:
        # [...]
        alternate_names: List[str] = ResourceRelationshipList(
            example=["alias 1", "alias 2"],
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(ExampleEnum),
        )
```

### Nested classes

If you have nested classes in your model definition, you will need to define a link to a 
separate class. We then have to define the separate ORM and logic classes ourselves. Let's say 
we want to describe this for our Example class:

```json
{
  "string_value": "foo",
  "nested": {
    "foo": "bar"
  }
}
```

Then we need to create `nested` in `src/database/model/example/nested.py`:

```python
from typing import TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:  # avoid circular imports; only import while type checking
    from database.model.example import Example


class NestedBase(SQLModel):
    foo: str | None = Field(max_length=150, schema_extra={"example": "Bar"})


class NestedORM(NestedBase, table=True):  # type: ignore [call-arg]
    __tablename__ = "nested"

    identifier: int | None = Field(primary_key=True)

    example_identifier: int | None = Field(foreign_key="example.identifier")
    example: "Example" = Relationship(back_populates="nested")


class Nested(NestedBase):
    pass
```

We can then add this to our `Example` model:

```python
class Example(ExampleBase, table=True):  # type: ignore [call-arg]
    # [...]
    nested: List[NestedORM] = Relationship(
        back_populates="examples", link_model=NestedLink
    )

    class RelationshipConfig:
        # [...]
        nested: List[Nested] = ResourceRelationshipList(
            deserializer=CastDeserializer(DataDownloadORM)
        )
```

See for a more complex example `dataset.data_download`.


## Router implementation
Create a router in `src/router`:

```python
from database.model.example import Example
from routers.resource_router import ResourceRouter


class ExampleRouter(ResourceRouter):
    @property
    def version(self) -> int:
        return 0

    @property
    def resource_name(self) -> str:
        return "example"

    @property
    def resource_name_plural(self) -> str:
        return "examples"

    @property
    def resource_class(self) -> type[Example]:
        return Example
```
And add it to `src/routers/__init__.py`. 

## Test
A lot of the routing is generic, but we want to test our new files. It is easy to make mistakes 
in the table relationships, for instance by mixing up a ORM model with a logic model.

Run the application and go to swagger. Click on the POST request and copy the json. If some 
fields are not correctly filled, improve the examples in your model.

Create a test file `src/tests/routers/test_router_example.py`, using your json. Base it, for 
instance, on `test_router_dataset.py`. Perform a POST and a GET, and test the fields that are 
linked to other tables. If this is correct, the rest should be OK because it depends on generic 
functionality. 

