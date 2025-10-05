from sqlalchemy import Column, String
from sqlmodel import SQLModel, Field

MAX_URL_LENGTH = 2000


# Unlike NamedRelation, URLs are:
#  - generally unique
#  - potentially much longer than the default 256 character limit
#  - case sensitive
class RelevantLink(SQLModel, table=True):  # type: ignore [call-arg]
    """An address of a resource on the web"""

    __tablename__ = "relevant_link"
    identifier: int = Field(default=None, primary_key=True)
    name: str = Field(
        sa_column=Column(
            String(length=MAX_URL_LENGTH)  # no collation: links may be case sensitive
        ),
        description="A URL for a page relevant to the resource.",
    )
