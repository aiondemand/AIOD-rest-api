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
    def match_fields(self):
        return set(['name', 'plain', 'html', 'headline', 'alternative_headline'])
