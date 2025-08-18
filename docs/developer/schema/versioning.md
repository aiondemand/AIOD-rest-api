from versioning import VersionedResourceCollection

# Versioning

???- tip "`Resource` and `Resource Object` definitions"

    On this page, the use of `resource` means the type of the asset, e.g., the `Dataset` type or the `Project` type.
    The term `(resource) object` may be used to define an instantiated object of some type.

!!! tip "Work in Progress"

    The `versioning` module that this page describes is work in progress, and is expected to change as we start using it to roll out changes.

While there is only ever one internal representation of any resource in the database, sometimes we need to allow different versions of that resource to be presented to the user. The most common example of this is for different versions of the REST API, where from version to version a resource may have different fields or change their types. So, we have the true resource representation (matching the class definition with `table=True`) and various views of the resource (generally defined as {AssetType}{VersionPrefix}{Create|Read}, e.g., `CaseStudyV3Read` or `ProjectCreate`).

To avoid manually defining each variation, often only differing by one or a few attributes, the `src/versioning` module adds some functionality to more easily make different versions of the schema.

## Versioning Metadata Objects
The `versioning.Version` enum defines all legal version values in the REST API. If it's not defined there, then it is not valid, not even if it is defined in the `versioning.toml` file.
Then, there are `VersionedResource`s which allow you to define how a resource (e.g., Project) should behave for a specific version. Please reference its docstring for a full description, but it essentially provides all the information the REST API needs to:

 - Provide schema definitions for the `Create` and `Read` schemas for that version of the asset type.
 - Transform a resource object from the database to the `Read` resource object for the given version.
 - Transform a `Create` resource object of the given representation to the database representation.

The `versioning` module also defines a `VersionedResourceCollection`, which is just a dictionary intended to map from a `Version` to a `VersionedResource`. This is added to each module which defines a resource.

## Example: Defining a VersionedResource

###  Defining the Schema Transformation

The `schema_transform` function of the `versioning` allows you to transform one schema to another by directly modifying the SQLModel representation to add, update, or remove fields.
Say you want to change the `given_name` field from the `Person` resource and rename it to `first_name`.
We can do this by creating two changes:

  - Add the `first_name` to the current schema,
  - Remove `given_name` from the current schema.

We must introduce a new version of the schema since removing a field is a [breaking change](#what-are-breaking-changes).
Let's assume that the last version with `given_name` was version 2.
We update the model:

```diff
class Person(...):
-    given_name: str = Field(...)
+    first_name: str = Field(...)
```

We define a transformation from the current representation to the old one:

```python
PersonV2Read = schema_transform(resource_read(Person), name="PersonV2Read", add_fields=dict(given_name=(str, Field(...))))
PersonV2Create = schema_transform(resource_create(Person), name="PersonV2Read", add_fields=dict(given_name=(str, Field(...))))
```

_note_: we're transforming the representations of the current `Read` and `Create` (e.g., `resource_read(Person)`), not the original resource schema. We do this because those functions already flatten the rich context of relationships and identifiers of the resource down to simple(r) fields.

### Defining the Data Transformation

Now we have an updated version for V2 of the _schema_ that has both `first_name` (it's part of the new Person) and a `given_name` (explicitly added back in with the snippet above). However, when a user requests a `ProjectV2Read` using a `GET` operation, or provides a `first_name` through the `ProjectV2Create`, it is ignored! We must inform the router how to transform the _data_.
We define these functions manually, first the `orm_to_read` function:

```python
def orm_to_read(person: Person) -> PersonV2Read:
    data = resource_read(Person).model_validate(person).model_dump()
    data['given_name'] = data['first_name']
    return PersonV2Read.model_validate(data)

```

The `data = resource_read(Person).model_validate(person).model_dump()` line of `orm_to_read` might look odd, but we want to only transform the data within the `Read` representation. By first loading it as a current-version `Read` object and dumping the model, we make sure that all the fields are represented through their regular serialization, e.g., transforming some relationships to identifiers while serializing others as objects. We can then manipulate this data to reflect the changes in the schema, in this case adding back in a `given_name` field.

For the `create_to_orm` method, it's slightly easier but we have to make sure that the _new_ name is populated even if the value is supplied under the old name. Values only present under the old name will be ignored when initializing the `Person` and thus not be stored.
```python
def create_to_orm(person: PersonV2Create) -> Person:
    data = person.model_dump()
    old_value = data.get("given_name")
    new_value = data.get("first_name")
    if (old_value and new_value) and old_value != new_value:
        raise ...  # two different values map to the same field
    data['first_name'] = old_value or new_value  # ensure the new field is set, the old isn't saved.
    return Person.model_validate(data)
```

### Creating the VersionedResource

Now we can register these changes under a new version in our persons module, e.g.:

```python

person_versions = VersionedResourceCollection({
    ...
    Version.V2: VersionedResource(
        Person,
        PersonV2Create,
        PersonV2Read,
        create_to_orm,
        orm_to_read,
    )
    ...
})

```
these different `VersionedResource` objects will be used to create routers for the assets.

## What are Breaking Changes?
We follow [these guidelines](https://docs.github.com/en/rest/about-the-rest-api/breaking-changes?apiVersion=2022-11-28#about-breaking-changes-in-the-rest-api) for identifying breaking changes.
In short, as far as model updates go, it is a breaking change if:

 - a field is removed
 - the type of a field changes
 - a new required field is added
 - an optional field is made required
 - enum values are removed

Notes:

 - a renamed field is essentially two changes; adding a new field and removing an old one.
It is possible to break these steps up in separate versions to allow a longer period of compatibility.
 - in this project, many times you expect an enum value we instead use a taxonomy. Taxonomy changes may happen at any time without warning, we have yet to determine transition behavior for that, though we can generally assume a taxonomy only expands in non-breaking fashion.

## Work In Progress
This document and the versioning module are work in progress.
We hope to iterate over it as we roll out different schema changes.
