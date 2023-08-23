"""
Functionality to generate a separate read resource and create resource. For example,
the date_modified should be in the read resource, but not in the the create resource. You should
not be able to modify this date yourself in a POST request, but you should retrieve it in a GET
request.
"""

from typing import Type, Tuple, TYPE_CHECKING

from pydantic import create_model
from sqlmodel import SQLModel, Field
from sqlmodel.main import FieldInfo

from database.model.helper_functions import all_annotations, get_relationships
from database.model.serializers import create_getter_dict

if TYPE_CHECKING:
    from database.model.concept.concept import AIoDConcept
    from database.model.relationships import ResourceRelationshipInfo


def _get_field_definitions_read(
    resource_class: Type["AIoDConcept"], relationships: dict[str, "ResourceRelationshipInfo"]
) -> dict[str, Tuple[Type, FieldInfo]]:
    if not hasattr(resource_class, "RelationshipConfig"):
        return {}
    annotations = all_annotations(resource_class.RelationshipConfig)
    return {
        attribute_name: (
            annotations[attribute_name]
            if config.class_read is None
            else config.class_read,  # the type
            config.field(),  # The Field()
        )
        for attribute_name, config in relationships.items()
    }


def _get_field_definitions_create(
    resource_class: Type["AIoDConcept"], relationships: dict[str, "ResourceRelationshipInfo"]
) -> dict[str, Tuple[Type, FieldInfo]]:
    if not hasattr(resource_class, "RelationshipConfig"):
        return {}
    annotations = all_annotations(resource_class.RelationshipConfig)
    return {
        attribute_name: (
            annotations[attribute_name]
            if config.class_create is None
            else config.class_create,  # the type
            config.field(),  # The Field()
        )
        for attribute_name, config in relationships.items()
        if config.include_in_create
    }


def resource_create(resource_class: Type["AIoDConcept"]) -> Type[SQLModel]:
    """
    Create a SQLModel for a Create class of a resource. This Create class is a Pydantic class
    that can be used for POST and PUT requests (and thus has no identifier), and is not backed by a
    ORM table.

    Besides the default attributes, this class has the Pydantic-version of the relationships. If the
    resource has a relationship to an "enum table", for instance, this will just be a string value
    in this Create class.

    See https://sqlmodel.tiangolo.com/tutorial/fastapi/multiple-models/ for background.
    """
    relationships = get_relationships(resource_class)
    field_definitions = _get_field_definitions_create(resource_class, relationships)

    model = create_model(
        resource_class.__name__ + "Create", __base__=resource_class.__base__, **field_definitions
    )
    return model


def resource_read(resource_class: Type["AIoDConcept"]) -> Type[SQLModel]:
    """
    Create a SQLModel for a Read class of a resource. This Read class is a Pydantic class
    that can be used for GET requests (and thus has a required identifier), and is not backed by a
    ORM table.

    Besides the default attributes, this class has the Pydantic-version of the relationships. If the
    resource has a relationship to an "enum table", for instance, this will just be a string value
    in this Read class.

    See https://sqlmodel.tiangolo.com/tutorial/fastapi/multiple-models/ for background.
    """
    relationships = get_relationships(resource_class)
    field_definitions = _get_field_definitions_read(resource_class, relationships)
    field_definitions.update({"identifier": (int, Field())})
    resource_class_read = create_model(
        resource_class.__name__ + "Read", __base__=resource_class.__base__, **field_definitions
    )
    _update_model_serialization(resource_class, resource_class_read)
    relationships.items()
    return resource_class_read


def _update_model_serialization(resource_class: Type[SQLModel], resource_class_read):
    """
    For every Serializer defined on the RelationshipConfig of the resource, use this Serializer in
    a newly created GetterDict (this is Pydantic functionality) and put in on the config of this
    resource.
    """
    relationships = get_relationships(resource_class)
    if hasattr(resource_class, "RelationshipConfig"):
        getter_dict = create_getter_dict(
            {
                attribute_name: relationshipConfig.serializer
                for attribute_name, relationshipConfig in relationships.items()
                if relationshipConfig.serializer is not None
            }
        )
        resource_class_read.__config__.getter_dict = getter_dict
