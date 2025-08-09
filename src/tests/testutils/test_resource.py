"""
Test resource with router and mocked converter
"""

from typing import Type

from sqlalchemy import String
from sqlmodel import Field

from database.model.concept.aiod_entry import AIoDEntryORM, EntryStatus
from database.model.concept.concept import AIoDConcept, AIoDConceptBase
from database.model.field_length import IDENTIFIER_LENGTH
from routers.resource_router import ResourceRouter


class TestResourceBase(AIoDConceptBase):
    title: str = Field(max_length=250, nullable=False)


class TestResource(TestResourceBase, AIoDConcept, table=True):  # type: ignore [call-arg]
    __abbreviation__ = "test"
    identifier: str = Field(max_length=IDENTIFIER_LENGTH, default=None, primary_key=True)


# Note that the alternative name `test_resource_factory` would make pytest pick this up as a unit test
def factory_test_resource(
    title="default_title", status=EntryStatus.DRAFT, platform="example", platform_resource_identifier="1", date_deleted=None
):
    return TestResource(
        title=title,
        platform=platform,
        platform_resource_identifier=platform_resource_identifier,
        aiod_entry=AIoDEntryORM(status=status),
        date_deleted=date_deleted,
    )


class RouterTestResource(ResourceRouter):
    """Router with only "aiod" as possible output format, used only for unittests"""

    @property
    def version(self) -> int:
        return 0

    @property
    def resource_name(self) -> str:
        return "test_resource"

    @property
    def resource_name_plural(self) -> str:
        return "test_resources"

    @property
    def resource_class(self) -> Type[TestResource]:
        return TestResource
