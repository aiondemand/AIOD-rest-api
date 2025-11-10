from enum import StrEnum, auto
from typing import Annotated

from fastapi import Query, Depends
from pydantic import BaseModel
from sqlmodel import Field


class SortDirection(StrEnum):
    ASC = auto()
    DESC = auto()


class Sort(StrEnum):
    DATE_CREATED = auto()
    DATE_MODIFIED = auto()


class Sorting(BaseModel):
    """Sorting modes for any AIoDConcept with an AIoD entry."""

    direction: SortDirection = Field(
        Query(
            description="The direction of the sort (ascending or descending).",
            default=SortDirection.DESC,
        )
    )
    sort: Sort = Field(
        Query(
            description="The property to sort by.",
            default=Sort.DATE_MODIFIED,
        )
    )


SortingParams = Annotated[Sorting, Depends(Sorting)]
