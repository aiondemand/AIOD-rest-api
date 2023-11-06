from typing import TYPE_CHECKING

from sqlmodel import SQLModel, Field

from database.model.field_length import SHORT

if TYPE_CHECKING:
    pass


class DatasetSizeBase(SQLModel):
    unit: str = Field(
        default=None,
        max_length=SHORT,
        description="Text indicating the unit of measurement.",
        schema_extra={"example": "Rows"},
    )
    value: int = Field(
        default=None,
        description="The size.",
        schema_extra={"example": 100},
    )


class DatasetSizeORM(DatasetSizeBase, table=True):  # type: ignore [call-arg]
    __tablename__ = "dataset_size"

    identifier: int = Field(default=None, primary_key=True)


class DatasetSize(DatasetSizeBase):
    """A point value for product characteristics"""
