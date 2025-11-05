from fastapi import Query, Depends, APIRouter

from authentication import KeycloakUser, get_user_or_none
from database.model.project.project import Project, project_versions
from dependencies.filtering import ResourceFiltersParams
from dependencies.pagination import PaginationParams
from routers.resource_routers.organisation_router import add_custom_routes
from routers.resource_router import ResourceRouter
from versioning import Version


class ProjectRouter(ResourceRouter):
    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "project"

    @property
    def resource_name_plural(self) -> str:
        return "projects"

    @property
    def resource_class(self) -> type[Project]:
        return Project

    # Redefined to add the `get_image` path parameter
    def get_resources_func(self):
        def get_resources(
            pagination: PaginationParams,
            resource_filters: ResourceFiltersParams,
            schema: self._possible_schemas_type = "aiod",  # type:ignore
            get_image: bool = Query(False, description="Include image bytes in response?"),
            user: KeycloakUser | None = Depends(get_user_or_none),
        ):
            return self.get_resources(
                schema=schema,
                pagination=pagination,
                resource_filters=resource_filters,
                user=user,
                get_image=get_image,
            )

        return get_resources

    # Redefined to add the `get_image` path parameter
    def get_resource_func(self):
        def get_resource(
            identifier: str,
            schema: self._possible_schemas_type = "aiod",  # type: ignore
            get_image: bool = Query(False, description="Include image bytes in response?"),
            user: KeycloakUser | None = Depends(get_user_or_none),
        ):
            resource = self.get_resource(
                identifier=identifier, schema=schema, user=user, platform=None, get_image=get_image
            )

            return resource

        return get_resource

    def create(self, url_prefix: str, version: Version = Version.LATEST) -> APIRouter:
        router = super().create(url_prefix)

        path = f"/{self.resource_name_plural}/{{identifier}}/image"
        add_custom_routes(self, router, path)

        return router


project_routers = {
    version: ProjectRouter(versioned_resource)
    for version, versioned_resource in project_versions.items()
}
