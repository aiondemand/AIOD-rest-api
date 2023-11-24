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

    def value(self, model: SQLModel, attribute_name):
        """Return the value, for most serializers just model.attribute_name"""
        return getattr(model, attribute_name)


class DeSerializer(abc.ABC, Generic[MODEL]):
    """Deserialization from ORM class to Pydantic class"""

    @abc.abstractmethod
    def deserialize(self, session: Session, serialized: Any) -> int | None | MODEL | List[MODEL]:
        pass


class AttributeSerializer(Serializer):
    """Serialize by using only the value of this attribute.

    For instance, if using `AttributeSerializer('identifier')`, only the identifier of this
    object will be shown to the user."""

    def __init__(self, attribute_name: str):
        self.attribute_name = attribute_name

    def serialize(self, model: MODEL) -> Any:
        return getattr(model, self.attribute_name)


class GetPathSerializer(Serializer):
    """
    Serializes to a nested path.

    E.g., dataset.has_path is serialized to dataset.ai_resource_identifier.has_path.
    """

    def __init__(self, path: str, inner_serializer: Serializer):
        self.path = path
        self.other_serializer = inner_serializer

    def serialize(self, model: MODEL) -> Any:
        return self.other_serializer.serialize(model)

    def value(self, model: SQLModel, attribute_name):
        """Return the value: model.[self.path].attribute_name"""
        inner_model = getattr(model, self.path)
        return getattr(inner_model, attribute_name)


@dataclasses.dataclass
class FindByIdentifierDeserializer(DeSerializer[SQLModel]):
    """
    Return a list of objects based on their identifiers.
    """

    clazz: type[SQLModel]

    def deserialize(self, session: Session, input_: int | None) -> SQLModel | None:
        if input_ is None:
            return None
        elif isinstance(input_, list):
            raise ValueError(
                "Expected a single value. Do you need to use "
                "FindByIdentifierDeserializerList instead?"
            )
        existing = FindByIdentifierDeserializer.deserialize_ids(self.clazz, session, [input_])
        (single_result,) = existing
        return single_result

    @staticmethod
    def deserialize_ids(clazz: type[SQLModel], session: Session, ids: list[int]):
        query = select(clazz).where(clazz.identifier.in_(ids))  # noqa
        existing = session.scalars(query).all()
        ids_not_found = set(ids) - {e.identifier for e in existing}
        if any(ids_not_found):
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Nested object with identifiers "
                f"{', '.join([str(i) for i in ids_not_found])} not found",
            )
        return existing


@dataclasses.dataclass
class FindByIdentifierDeserializerList(DeSerializer[SQLModel]):
    """
    Return a list of objects based on their identifiers.
    """

    clazz: type[SQLModel]

    def deserialize(self, session: Session, input_: list[int] | None) -> list[SQLModel]:
        if isinstance(input_, int):
            raise ValueError("Expected a list. Do you need to use FindByNameDeserializer instead?")
        elif input_ is None or len(input_) == 0:
            return []
        existing = FindByIdentifierDeserializer.deserialize_ids(self.clazz, session, input_)
        return sorted(existing, key=lambda o: o.identifier)


@dataclasses.dataclass
class FindByNameDeserializer(DeSerializer[NamedRelation]):
    """Deserialization of NamedRelations: uniquely identified by their name."""

    clazz: type[NamedRelation]

    def deserialize(self, session: Session, name: str | None) -> int | None:
        if name is None:
            return None
        if isinstance(name, list):
            raise ValueError(
                "Expected a single value. Do you need to use " "FindByNameDeserializerList instead?"
            )
        name = name.lower()
        query = select(self.clazz.identifier).where(self.clazz.name == name)
        identifier = session.scalars(query).first()
        if identifier is None:
            new_object = self.clazz(name=name)
            session.add(new_object)
            session.flush()
            identifier = new_object.identifier
        return identifier


@dataclasses.dataclass
class FindByNameDeserializerList(DeSerializer[NamedRelation]):
    """Deserialization of NamedRelations: uniquely identified by their name."""

    clazz: type[NamedRelation]

    def deserialize(self, session: Session, name: list[str] | None) -> list[NamedRelation]:
        if name is None:
            return []
        if not isinstance(name, list):
            raise ValueError("Expected a list. Do you need to use FindByNameDeserializer instead?")
        names = [n.lower() for n in name]
        query = select(self.clazz).where(self.clazz.name.in_(names))  # type: ignore[attr-defined]
        existing = session.scalars(query).all()
        names_not_found = set(names) - {e.name for e in existing}
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

    def deserialize(self, session: Session, serialized: Any) -> None | SQLModel:
        if serialized is None:
            return None
        if isinstance(serialized, list):
            raise ValueError(
                "Expected a single value. Do you need to use CastDeserializerList " "instead?"
            )
        return self._deserialize_single_resource(serialized, session)

    def _deserialize_single_resource(self, serialized, session):
        resource = self.clazz.from_orm(serialized)
        deserialize_resource_relationships(session, self.clazz, resource, serialized)
        return resource


class CastDeserializerList(CastDeserializer):
    """
    Deserialize by casting it to a class.
    """

    clazz: type[SQLModel]

    def deserialize(self, session: Session, serialized: list | None) -> list[SQLModel]:
        if serialized is None:
            return []
        if not isinstance(serialized, list):
            raise ValueError("Expected a list. Do you need to use CastDeserializer instead?")
        return [self._deserialize_single_resource(v, session) for v in serialized]


def create_getter_dict(attribute_serializers: Dict[str, Serializer]):
    """Based on a dictionary of `variable_name, Serializer`, generate a `getter_dict`. A
    `getter_dict` is used by Pydantic to perform serialization.

    We have added a layer of Serializers instead of directly using a getter_dict, to make it
    easier to configure the serialization per object attribute, instead of for each complete
    object."""
    attribute_names = set(attribute_serializers.keys())

    class GetterDictSerializer(GetterDict):
        def get(self, key: Any, default: Any = None) -> Any:
            # if key == "has_part" and hasattr(self._obj, "ai_resource"):
            #     return [p.identifier for p in self._obj.ai_resource.has_part]
            if key in attribute_names:
                serializer = attribute_serializers[key]
                attribute_value = serializer.value(model=self._obj, attribute_name=key)
                if attribute_value is not None:
                    if isinstance(attribute_value, list):
                        return [serializer.serialize(v) for v in attribute_value]
                    return serializer.serialize(attribute_value)
            return super().get(key, default)

    return GetterDictSerializer


def deserialize_resource_relationships(
    session: Session,
    resource_class: Type[SQLModel],
    resource: SQLModel,
    resource_create_instance: SQLModel,
):
    """After deserialization of a resource, this function will deserialize all it's related
    objects in place."""
    if not hasattr(resource_class, "RelationshipConfig") or resource_create_instance is None:
        return
    relationships = get_relationships(resource_class)
    for attribute, relationship in relationships.items():
        if relationship.deserialized_path is None:
            new_value = None
            do_update_value = False
            if (
                isinstance(relationship.deserializer, CastDeserializer)
                and hasattr(resource, attribute)
                and getattr(resource, attribute)
            ):
                deserialize_object_relationship(
                    session, resource, resource_create_instance, attribute
                )
            elif relationship.include_in_create:
                do_update_value = True
                new_value = getattr(resource_create_instance, attribute)
                if new_value is None and relationship.default_factory_orm is not None:
                    # e.g. .aiod_entry, which should be generated if it's not present
                    relation = relationship.default_factory_orm(type_=resource_class.__tablename__)
                    session.add(relation)
                    session.flush()
                    new_value = relation
            else:
                # This attribute is not included in the "create instance". In other words,
                # it is not part of the json specified in a POST or PUT request. Examples are
                # Dataset.asset_identifier. This identifier is assigned by the AIoD platform,
                # not by the user.
                if getattr(resource, attribute) is not None:
                    # The attribute is already set (so this is a PUT request). Keep existing value
                    pass
                elif relationship.default_factory_orm is not None:
                    if not hasattr(relationship, "identifier_name"):
                        raise ValueError()
                    relation = relationship.default_factory_orm(type_=resource_class.__tablename__)
                    session.add(relation)
                    session.flush()
                    setattr(resource, attribute, relation)
                    setattr(resource, relationship.identifier_name, relation.identifier)

            if do_update_value:
                if relationship.deserializer is not None:
                    new_value = relationship.deserializer.deserialize(session, new_value)
                setattr(resource, relationship.attribute(attribute), new_value)

    for attribute, relationship in relationships.items():
        if relationship.deserialized_path is not None:
            new_value = getattr(resource_create_instance, attribute)
            if relationship.deserializer:
                new_value = relationship.deserializer.deserialize(session, new_value)
            inner_model = getattr(resource, relationship.deserialized_path)
            setattr(inner_model, attribute, new_value)


def deserialize_object_relationship(session, resource, resource_create_instance, attribute):
    """
    In place deserialization of an object relationship (a relationship to an object that is
    completely present in the json, instead of linked using an identifier).

    e.g., AIoDEntry or AIoDResource.
    """
    children = getattr(resource, attribute)
    children_create = getattr(resource_create_instance, attribute)
    if not isinstance(children, list):
        children = [children]
        children_create = [children_create]
    child_class = type(children[0])
    for child, child_create in zip(children, children_create):
        for child_attribute in child_class.schema()["properties"]:
            if hasattr(child_create, child_attribute):
                child_value = getattr(child_create, child_attribute)
                setattr(child, child_attribute, child_value)
        deserialize_resource_relationships(session, child_class, child, child_create)
    n_create = len(children_create)
    for child in children[n_create:]:
        session.delete(child)
    n_existing = len(children)
    for child_create in children_create[n_existing:]:
        child = child_class.from_orm(child_create)
        deserialize_resource_relationships(session, child_class, child, child_create)
        children.append(child)
