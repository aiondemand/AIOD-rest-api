from database.model.named_relation import NamedRelation


class NewsCategory(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "news_category"
