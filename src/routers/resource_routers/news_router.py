from database.model.news.news import News, news_versions
from routers.resource_router import ResourceRouter


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
    version: NewsRouter(versioned_resource) for version, versioned_resource in news_versions.items()
}
