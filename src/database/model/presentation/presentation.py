from sqlmodel import Field
from datetime import datetime

from database.model.ai_asset import AIAssetOld


class PresentationBase(AIAssetOld):
    # Required fields
    name: str = Field(max_length=150, schema_extra={"example": "Example Presentation"})

    description: str = Field(max_length=5000, schema_extra={"example": "A description."})
    # Recommended fields
    url: str | None = Field(
        max_length=250,
        default=None,
        schema_extra={"example": "https://example.com/presentation/example/description"},
    )
    datePublished: datetime | None = Field(
        default=None, schema_extra={"example": "2022-01-01T15:15:00.000Z"}
    )
    publisher: str | None = Field(
        max_length=150, default=None, schema_extra={"example": "John Doe"}
    )
    author: str | None = Field(max_length=250, default=None, schema_extra={"example": "John Doe"})
    image: str | None = Field(
        max_length=250,
        default=None,
        schema_extra={"example": "https://example.com/presentation/example/image"},
    )
    is_accessible_for_free: bool = Field(default=True)


class Presentation(PresentationBase, table=True):  # type: ignore [call-arg]
    __tablename__ = "presentations"

    identifier: int = Field(primary_key=True, foreign_key="ai_asset.identifier")
