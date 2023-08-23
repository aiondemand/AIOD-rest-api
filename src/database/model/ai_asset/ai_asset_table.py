from sqlmodel import Field, SQLModel


class AIAssetTable(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "ai_asset"
    identifier: int = Field(default=None, primary_key=True)
    type: str = Field(
        description="The name of the table of the asset. E.g. 'organisation' or 'member'"
    )
