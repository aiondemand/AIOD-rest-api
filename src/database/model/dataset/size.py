from sqlmodel import SQLModel, Field

from database.model.field_length import SHORT


class SizeBase(SQLModel):
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


class SizeORM(SizeBase, table=True):  # type: ignore [call-arg]
    __tablename__ = "size"

    identifier: int = Field(default=None, primary_key=True)


class Size(SizeBase):
    """A point value for product characteristics"""
