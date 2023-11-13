"""
The external platform (e.g. openml).
"""


import datetime

from sqlmodel import Field, SQLModel


class PlatformBase(SQLModel):
    name: str = Field(
        description="The name of the platform, such as huggingface, "
        "openml or zenodo. Preferably using snake_case.",
        schema_extra={"example": "example_platform"},
        index=True,
        unique=True,
    )


class Platform(PlatformBase, table=True):  # type: ignore [call-arg]
    """The external platforms such as HuggingFace, OpenML and Zenodo that have connectors to
    AIoD. This table is partly filled with the enum PlatformName"""

    __tablename__ = "platform"
    __deletion_config__ = {"soft_delete": False}  # hard_deletion, otherwise name cannot be unique,
    # which is difficult for foreign key constraints

    identifier: int = Field(primary_key=True, default=None)
    date_deleted: datetime.datetime | None = Field()
