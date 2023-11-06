import abc
import dataclasses
from typing import Any, TypeVar, Generic, Dict, List, Type

from fastapi import HTTPException
from pydantic.utils import GetterDict
from sqlmodel import SQLModel, Session, select
from starlette.status import HTTP_404_NOT_FOUND

from database.model.helper_functions import get_relationships
from database.model.named_relation import NamedRelation


MODEL = TypeVar("MODEL", bound=SQLModel)


class Serializer(abc.ABC, Generic[MODEL]):
    """Serialization from Pydantic class to ORM class"""

    @abc.abstractmethod
    def serialize(self, model: MODEL) -> Any:
        pass


class DeSerializer(abc.ABC, Generic[MODEL]):
    """Deserialization from ORM class to Pydantic class"""

    @abc.abstractmethod
    def deserialize(self, session: Session, serialized: Any) -> MODEL | List[MODEL]:
        pass


class AttributeSerializer(Serializer):
    """Serialize by using only the value of this attribute.

    For instance, if using `AttributeSerializer('identifier')`, only the identifier of this
    object will be shown to the user."""

    def __init__(self, attribute_name: str):
        self.attribute_name = attribute_name

    def serialize(self, model: MODEL) -> Any:
        return getattr(model, self.attribute_name)


@dataclasses.dataclass
class FindByIdentifierDeserializer(DeSerializer[SQLModel]):
    """
    Return a list of objects based on their identifiers.
    """

    clazz: type[SQLModel]

    def deserialize(self, session: Session, ids: list[int]) -> list[SQLModel]:
        if not isinstance(ids, list):
            raise ValueError("Expected list. This deserializer is not needed for single values.")
        query = select(self.clazz).where(self.clazz.identifier.in_(ids))  # noqa
        existing = session.scalars(query).all()
        ids_not_found = set(ids) - {e.identifier for e in existing}
        if any(ids_not_found):
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Nested object with identifiers "
                f"{', '.join([str(i) for i in ids_not_found])} not found",
            )
        return sorted(existing, key=lambda o: o.identifier)


@dataclasses.dataclass
class FindByNameDeserializer(DeSerializer[NamedRelation]):
    """
    Deserialization of NamedValues: uniquely identified by their name.

    In case of a single name, this deserializer returns the identifier. In case of a list of
    names, it returns the list of NamedValues.
    """

    clazz: type[NamedRelation]

    def deserialize(
        self, session: Session, name: str | list[str]
    ) -> NamedRelation | list[NamedRelation]:
        if not isinstance(name, list):
            query = select(self.clazz.identifier).where(self.clazz.name == name)
            identifier = session.scalars(query).first()
            if identifier is None:
                new_object = self.clazz(name=name)
                session.add(new_object)
                session.flush()
                identifier = new_object.identifier
            return identifier

        query = select(self.clazz).where(self.clazz.name.in_(name))  # type: ignore[attr-defined]
        existing = session.scalars(query).all()
        names_not_found = set(name) - {e.name for e in existing}
        new_objects = [self.clazz(name=name) for name in names_not_found]
        if any(names_not_found):
            session.add_all(new_objects)
            session.flush()
        return sorted(existing + new_objects, key=lambda o: o.identifier)


@dataclasses.dataclass
class CastDeserializer(DeSerializer[SQLModel]):
    """
    Deserialize by casting it to a class.
    """

    clazz: type[SQLModel]

    def deserialize(self, session: Session, serialized: Any) -> SQLModel | List[SQLModel]:
        if not isinstance(serialized, list):
            return self._deserialize_single_resource(serialized, session)
        return [self._deserialize_single_resource(v, session) for v in serialized]

    def _deserialize_single_resource(self, serialized, session):
        resource = self.clazz.from_orm(serialized)
        deserialize_resource_relationships(session, self.clazz, resource, serialized)
        return resource


def create_getter_dict(attribute_serializers: Dict[str, Serializer]):
    """Based on a dictionary of `variable_name, Serializer`, generate a `getter_dict`. A
    `getter_dict` is used by Pydantic to perform serialization.

    We have added a layer of Serializers instead of directly using a getter_dict, to make it
    easier to configure the serialization per object attribute, instead of for each complete
    object."""
    attribute_names = set(attribute_serializers.keys())

    class GetterDictSerializer(GetterDict):
        def get(self, key: Any, default: Any = None) -> Any:
            if key in attribute_names:
                attribute = getattr(self._obj, key)
                if attribute is not None:
                    serializer = attribute_serializers[key]
                    if isinstance(attribute, list):
                        return [serializer.serialize(v) for v in attribute]
                    return serializer.serialize(attribute)
            return super().get(key, default)

    return GetterDictSerializer


def deserialize_resource_relationships(
    session: Session,
    resource_class: Type[SQLModel],
    resource: SQLModel,
    resource_create_instance: SQLModel,
):
    """After deserialization of a resource, this function will deserialize all it's related
    objects."""
    if hasattr(resource_class, "RelationshipConfig"):
        relationships = get_relationships(resource_class)
        for attribute, relationship in relationships.items():
            if relationship.include_in_create:
                new_value = getattr(resource_create_instance, attribute)
            else:
                # This attribute is not included in the "create instance". In other words,
                # it is not part of the json specified in a POST or PUT request. Examples are
                # Dataset.resource_identifier. This identifier is assigned by the AIoD platform,
                # not by the user.
                if getattr(resource, attribute) is not None:
                    # The attribute is already set (so this is a PUT request). Keep existing value
                    new_value = None
                elif relationship.default_factory_orm is None:
                    raise ValueError(
                        "If a relationship is not included in create, it should contain a "
                        "default_factory_orm"
                    )
                else:
                    parent = relationship.default_factory_orm(type_=resource_class.__tablename__)
                    session.add(parent)
                    session.flush()
                    new_value = parent.identifier
            if new_value is not None:
                if relationship.deserializer is not None:
                    new_value = relationship.deserializer.deserialize(session, new_value)
                if hasattr(relationship, "identifier_name") and relationship.identifier_name:
                    setattr(resource, relationship.identifier_name, new_value)
                else:
                    setattr(resource, attribute, new_value)
