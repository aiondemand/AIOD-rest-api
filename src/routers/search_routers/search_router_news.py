from database.model.news.news import News
from routers.search_router import SearchRouter


class SearchRouterNews(SearchRouter[News]):
    @property
    def es_index(self) -> str:
        return "news"

    @property
    def resource_name_plural(self) -> str:
        return "news"

    @property
    def resource_class(self):
        return News

    @property
    def indexed_fields(self):
        return {"name", "description_plain", "description_html", "headline", "alternative_headline"}

    @property
    def linked_fields(self):
        return {}
