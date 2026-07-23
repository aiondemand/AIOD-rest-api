import dataclasses
from typing import TypeVar, Generic, List

from sqlmodel import SQLModel

from database.model.concept.concept import AIoDConcept
from database.model.annotations import datatype_of_field

RESOURCE = TypeVar("RESOURCE", bound=SQLModel)


@dataclasses.dataclass
class ResourceWithRelations(Generic[RESOURCE]):
    """
    A resource, with related AIResources in a dictionary of {field_name: other resource(s)}.
    """

    resource: RESOURCE
    resource_ORM_class: type[SQLModel]
    related_resources: dict[str, AIoDConcept | List[AIoDConcept]] = dataclasses.field(
        default_factory=dict
    )
    # For each field name, another resource or a list of other resources

    def __post_init__(self):
        """
        Raise an error if there is a mismatch between the datatype of a related resource,
        and the datatype of the corresponding field. For example, for Dataset.creator,
        the datatype is list[Contact] according to the annotations. Therefore, related resources
        with the key "creator" should be of datetype "ContactCreate".
        """
        for name, resource_values in self.related_resources.items():
            # ToDo:We could use from __future__ import annotations instead of using string-types.
            # Refer:https://stackoverflow.com/questions/33837918/type-hints-solve-circular-dependency
            name_type = datatype_of_field(clazz=self.resource_ORM_class, field_name=name)
            if not isinstance(
                name_type, str
            ):  # the datatype will be string, if the annotation List["Publication"]
                name_type = name_type.__name__

            resource_values = (
                resource_values if isinstance(resource_values, list) else [resource_values]
            )

            for resource_value in resource_values:
                name_expected = f"{name_type}Create"
                #  type(resource_value) returns class, ex: <class 'pydantic.main.PublicationCreate'>
                name_actual = type(resource_value).__name__
                if name_expected != name_actual:
                    raise ValueError(
                        f"Type mismatch for field '{self.resource_ORM_class.__name__ + '.' + name}'. \
                            Expected {name_expected}, got {name_actual}."  # noqa: E501
                    )
