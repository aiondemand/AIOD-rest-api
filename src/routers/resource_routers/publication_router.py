from database.model.knowledge_asset.publication import Publication
from routers.resource_ai_asset_router import ResourceAIAssetRouter


class PublicationRouter(ResourceAIAssetRouter):
    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "publication"

    @property
    def resource_name_plural(self) -> str:
        return "publications"

    @property
    def resource_class(self) -> type[Publication]:
        return Publication
