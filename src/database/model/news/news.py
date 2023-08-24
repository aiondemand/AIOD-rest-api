from sqlmodel import Field

from database.model.ai_resource.resource import AIResource, AIResourceBase
from database.model.field_length import NORMAL


class NewsBase(AIResourceBase):
    headline: str | None = Field(
        description="A short headline given to this news item.",
        max_length=NORMAL,
        schema_extra={"example": "A headline to show on top of the page."},
    )
    alternative_headline: str | None = Field(
        description="An alternative headline given to this news item.",
        max_length=NORMAL,
        schema_extra={"example": "An alternative headline."},
    )


class News(NewsBase, AIResource, table=True):  # type: ignore [call-arg]
    __tablename__ = "news"

    # Instead of related assets, projects and news, as suggested by the spreadsheet, we propose
    # to use News.has_part (pointing to AIResource)
