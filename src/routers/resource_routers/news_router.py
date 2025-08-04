from database.model.news.news import News
from routers.resource_router import ResourceRouter
from versioning import Version


class NewsRouter(ResourceRouter):
    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "news"

    @property
    def resource_name_plural(self) -> str:
        return "news"

    @property
    def resource_class(self) -> type[News]:
        return News


news_routers = {
    Version.V2: NewsRouter(),
    Version.LATEST: NewsRouter(),
}
