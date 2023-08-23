from sqlmodel import SQLModel, Field


class AgentTable(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "agent"
    identifier: int = Field(default=None, primary_key=True)
    type: str = Field(
        description="The name of the table of the resource. E.g. 'organisation' or 'person'"
    )
