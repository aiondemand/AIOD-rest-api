from sqlmodel import Field, SQLModel

from database.model.field_length import IDENTIFIER_LENGTH
from database.identifiers import create_id_generator


class AIAssetTable(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "ai_asset"
    identifier: str = Field(
        default_factory=create_id_generator(), max_length=IDENTIFIER_LENGTH, primary_key=True
    )
    type: str = Field(
        description="The name of the table of the asset. E.g. 'organisation' or 'member'"
    )
