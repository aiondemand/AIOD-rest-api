from typing import Annotated, Sequence, TypeVar, Generic

from fastapi import Query, Depends
from pydantic import BaseModel
from pydantic.generics import GenericModel
from sqlmodel import Field


class Pagination(BaseModel):
    """Offset-based pagination."""

    offset: int = Field(
        Query(
            description="Specifies the number of resources that should be skipped.", default=0, ge=0
        )
    )
    # Query inside field to ensure description is shown in Swagger.
    # Refer to https://github.com/tiangolo/fastapi/issues/4700
    limit: int = Field(
        Query(
            description="Specified the maximum number of resources that should be returned.",
            default=10,
            le=1000,
        )
    )


PaginationParams = Annotated[Pagination, Depends(Pagination)]

T = TypeVar("T")

class PaginatedResponse(GenericModel, Generic[T]):
    offset: int
    limit: int
    total_count: int
    data: Sequence[T]
