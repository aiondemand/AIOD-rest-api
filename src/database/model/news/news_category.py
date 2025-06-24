from database.model.named_relation import Taxonomy


class NewsCategory(Taxonomy, table=True):  # type: ignore [call-arg]
    __tablename__ = "news_category"
