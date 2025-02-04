from database.model.computational_asset.computational_asset import ComputationalAsset
from routers.search_router import SearchRouter


class SearchRouterComputationalAsset(SearchRouter[ComputationalAsset]):
    @property
    def es_index(self) -> str:
        return "computational_asset"

    @property
    def resource_name_plural(self) -> str:
        return "computational_assets"

    @property
    def resource_class(self):
        return ComputationalAsset
