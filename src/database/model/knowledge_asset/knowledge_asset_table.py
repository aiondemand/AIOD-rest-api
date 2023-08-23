from sqlmodel import Field, SQLModel


class KnowledgeAssetTable(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "knowledge_asset"
    identifier: int = Field(default=None, primary_key=True)
    type: str = Field(
        description="The name of the table of the knowledge asset. E.g. 'publication'"
    )
