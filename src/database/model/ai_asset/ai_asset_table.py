from sqlmodel import Field, SQLModel

from database.model.field_length import IDENTIFIER_LENGTH
from database.identifiers import create_id_generator, IDENTIFIER_TYPE


class AIAssetTable(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "ai_asset"
    identifier: str = Field(
        default_factory=create_id_generator(),
        max_length=IDENTIFIER_LENGTH,
        sa_type=IDENTIFIER_TYPE,
        primary_key=True,
    )
    type: str = Field(
        description="The name of the table of the asset. E.g. 'organisation' or 'member'"
    )
