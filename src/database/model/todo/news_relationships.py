# import typing  # noqa:F401 (flake8 raises incorrect 'Module imported but unused' error)
#
# from sqlalchemy import ForeignKey, Table, Column
#
# from database.model.base import Base
#
# news_business_category_relationship = Table(
#     "news_business_category",
#     Base.metadata,
#     Column("news_id", ForeignKey("news.identifier", ondelete="CASCADE"), primary_key=True),
#     Column(
#         "business_category_id",
#         ForeignKey("business_categories.identifier", ondelete="CASCADE"),
#         primary_key=True,
#     ),
# )
#
# news_keyword_relationship = Table(
#     "news_keyword",
#     Base.metadata,
#     Column(
#         "news_id",
#         ForeignKey("news.identifier", ondelete="CASCADE", onupdate="RESTRICT"),
#         primary_key=True,
#     ),
#     Column(
#         "keyword_id",
#         ForeignKey("keywords.identifier", ondelete="CASCADE", onupdate="RESTRICT"),
#         primary_key=True,
#     ),
# )
#
# news_news_category_relationship = Table(
#     "news_news_category",
#     Base.metadata,
#     Column("news_id", ForeignKey("news.identifier", ondelete="CASCADE"), primary_key=True),
#     Column(
#         "news_category_id",
#         ForeignKey("news_categories.identifier", ondelete="CASCADE"),
#         primary_key=True,
#     ),
# )
#
# news_media_relationship = Table(
#     "news_media",
#     Base.metadata,
#     Column("news_id", ForeignKey("news.identifier", ondelete="CASCADE"), primary_key=True),
#     Column("media_id", ForeignKey("media.identifier", ondelete="CASCADE"), primary_key=True),
# )