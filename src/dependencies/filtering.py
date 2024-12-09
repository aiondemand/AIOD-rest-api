import datetime
from typing import Annotated

from fastapi import Query, Depends
from pydantic import BaseModel
from sqlmodel import Field


class ResourceFilters(BaseModel):
    """Resource filters used in GET endpoints"""

    date_modified_after: datetime.date | None = Field(
        Query(
            description="Get only resources modified after this date (yyyy-mm-dd, inclusive).",
            default=None,
        )
    )
    date_modified_before: datetime.date | None = Field(
        Query(
            description="Get only resources modified before this date (yyyy-mm-dd, exclusive).",
            default=None,
        )
    )


ResourceFiltersParams = Annotated[ResourceFilters, Depends(ResourceFilters)]
