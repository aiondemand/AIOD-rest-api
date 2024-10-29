"""
Helper functions for the annotations of python classes. This can for instance be used to get all
fields of a class (e.g. identifier, name etc. for Dataset) and their datatype.
"""
import inspect
from collections import ChainMap
from typing import Type, ForwardRef

import typing_inspect
from sqlalchemy.orm.util import _is_mapped_annotation, _extract_mapped_subtype
from sqlmodel import SQLModel


def all_annotations(cls) -> ChainMap:
    """Returns a dictionary-like ChainMap that includes annotations for all
    attributes defined in cls or inherited from superclasses.

    From
    https://stackoverflow.com/questions/63903901/how-can-i-access-to-annotations-of-parent-class
    """
    return ChainMap(*(inspect.get_annotations(c) for c in cls.mro()))


def datatype_of_field(clazz: Type[SQLModel], field_name: str) -> Type | str:
    """
    Returns the datatype of a field, based on the annotations. It returns the inner type in case
    of a list, or an optional. Returns a str in case a forward reference was used.

    Examples:
    - name: str                     returns str
    - issn: str | None              returns str
    - funder: list[AgentTable]      returns AgentTable
    - funder: list["AgentTable"]    returns "AgentTable"
    """
    annotation = inspect.get_annotations(clazz)[field_name]

    # The content of this first if-statement is copied from SQLAlchemy's inner code.
    if _is_mapped_annotation(annotation, clazz, clazz):
        extracted = _extract_mapped_subtype(
            annotation,
            clazz,
            clazz.__module__,
            field_name,
            attr_cls=type(None),
            required=False,
            is_dataclass_field=False,
            expect_mapped=False,
        )
        if extracted:
            inner, _ = extracted
            annotation = inner
    if typing_inspect.is_optional_type(annotation):  # e.g. Optional[Dataset]
        (annotation,) = [
            part
            for part in typing_inspect.get_args(annotation)
            if not typing_inspect.is_optional_type(part)
        ]
    if typing_inspect.is_generic_type(annotation):  # e.g. List[Dataset]
        (annotation,) = typing_inspect.get_args(annotation)
    if isinstance(annotation, ForwardRef):
        annotation = annotation.__forward_arg__
    return annotation
