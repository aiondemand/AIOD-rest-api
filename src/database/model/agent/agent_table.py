from sqlmodel import SQLModel, Field

from database.model.field_length import IDENTIFIER_LENGTH
from database.identifiers import create_id_generator


class AgentTable(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "agent"
    identifier: str = Field(
        max_length=IDENTIFIER_LENGTH,
        default_factory=create_id_generator(),
        primary_key=True,
    )
    type: str = Field(
        description="The name of the table of the resource. E.g. 'organisation' or 'person'"
    )
