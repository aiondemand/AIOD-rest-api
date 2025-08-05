from database.model.computational_asset.computational_asset import (
    ComputationalAsset,
    computational_asset_versions,
)

from routers.resource_router import ResourceRouter


class ComputationalAssetRouter(ResourceRouter):
    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "computational_asset"

    @property
    def resource_name_plural(self) -> str:
        return "computational_assets"

    @property
    def resource_class(self) -> type[ComputationalAsset]:
        return ComputationalAsset


computational_asset_routers = {
    version: ComputationalAssetRouter(versioned_resource)
    for version, versioned_resource in computational_asset_versions.items()
}
