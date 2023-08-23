from sqlmodel import SQLModel, Field


class AIResourceTable(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "ai_resource"
    identifier: int = Field(default=None, primary_key=True)
    type: str = Field(
        description="The name of the table of the resource. E.g. 'organisation' or 'member'"
    )
