import datetime

from sqlmodel import Field, SQLModel


class PlatformBase(SQLModel):
    name: str = Field(
        unique=True,
        description="The name of the platform, such as huggingface, "
        "openml or zenodo. Preferably using snake_case.",
        schema_extra={"example": "example_platform"},
        index=True,
    )
    date_deleted: datetime.datetime | None = Field()


class Platform(PlatformBase, table=True):  # type: ignore [call-arg]
    """The external platforms such as HuggingFace, OpenML and Zenodo that have connectors to
    AIoD. This table is partly filled with the enum PlatformName"""

    __tablename__ = "platform"

    identifier: int = Field(primary_key=True, default=None)
