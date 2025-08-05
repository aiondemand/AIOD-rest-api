from database.model.resource_bundle.resource_bundle import ResourceBundle, resource_bundle_versions
from routers.resource_router import ResourceRouter


class ResourceBundleRouter(ResourceRouter):
    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "resource_bundle"

    @property
    def resource_name_plural(self) -> str:
        return "resource_bundles"

    @property
    def resource_class(self) -> type[ResourceBundle]:
        return ResourceBundle


resource_bundle_routers = {
    version: ResourceBundleRouter(versioned_resource)
    for version, versioned_resource in resource_bundle_versions.items()
}
