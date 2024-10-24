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
    def extra_indexed_fields(self) -> set[str]:
        return {"headline", "alternative_headline"}
