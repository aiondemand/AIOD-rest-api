from database.model.agent.organisation import Organisation, organisation_versions
from routers.resource_router import ResourceRouter
from fastapi import UploadFile, File, HTTPException, Query, status, APIRouter, Depends
from http import HTTPStatus
from sqlmodel import select, Session
from database.model.agent.organisation import Organisation
from database.session import get_session
import base64
from authentication import KeycloakUser, get_user_or_none, get_user_or_raise
from dependencies.filtering import ResourceFiltersParams
from dependencies.pagination import PaginationParams
from database.model.concept.aiod_entry import EntryStatus
from database.authorization import (
    user_can_administer,
    user_can_write,
)
import datetime
from error_handling import as_http_exception
from versioning import Version

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp"}
MAX_FILE_SIZE_BYTES = 1 * 1024 * 1024  # 1MB


class OrganisationRouter(ResourceRouter):
    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "organisation"

    @property
    def resource_name_plural(self) -> str:
        return "organisations"

    @property
    def resource_class(self) -> type[Organisation]:
        return Organisation

    def validate_image_type(self, file: UploadFile):
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type {file.content_type}. Allowed image types: {ALLOWED_IMAGE_TYPES}.",
            )

    def _get_resource(self, session: Session, identifier: str) -> Organisation:
        resource = session.exec(
            select(Organisation).where(Organisation.identifier == identifier)
        ).one_or_none()
        if not resource:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Organisation {identifier} not found in the database.",
            )
        return resource

    def _check_user_can_edit(self, user: KeycloakUser, resource: Organisation, resource_name: str):
        if not (
            user_can_write(user, resource.aiod_entry)
            or user.has_role(f"update_{self.resource_name_plural}")
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have permission to edit {self.resource_name_plural}.",
            )

        if resource.aiod_entry.status == EntryStatus.SUBMITTED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot edit an asset under submission.",
            )

    async def read_image_file(self, file: UploadFile) -> bytes:
        blob = await file.read()
        if len(blob) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                detail="File too large (max 1MB).",
            )
        return blob

    def add_custom_routes(self, router: APIRouter, path: str):
        """ "
        Organisation image endpoints.

        Currently supports POST, PUT, GET, DELETE (image blob, ex. logo) for an Organisation.
        This is the only resource with image support at the moment,
        but the logic can be extended to other resource types in the future if needed.
        """

        @router.post(path, tags=[self.resource_name_plural])
        async def organisation_image(
            identifier: str,
            file: UploadFile = File(...),
            name: str = Query(..., description="Uploaded image filename", example="logo"),
            session=Depends(get_session),
            user: KeycloakUser | None = Depends(get_user_or_raise),
        ):
            self.validate_image_type(file)

            try:
                resource = self._get_resource(session, identifier)

                self._check_user_can_edit(user, resource, self.resource_name_plural)

                # Donot allow image upload with same name.
                # We do not check for identical image content (only name).
                # Consider adding a limit on the number of uploaded images in the future.

                if any(media.name == name for media in resource.media):
                    raise HTTPException(
                        status_code=HTTPStatus.CONFLICT,
                        detail=f"An image with the name '{name}' already exists for this organisation.",
                    )

                blob = await self.read_image_file(file)

                media_cls = resource.__class__.media.property.mapper.class_

                media = media_cls(binary_blob=blob, name=name, encoding_format=file.content_type)
                resource.media.append(media)

                try:
                    session.add(media)
                    session.add(resource)
                    session.commit()
                except Exception as e:
                    self._raise_clean_http_exception(e, session, resource)
                return {"identifier": resource.identifier}

            except Exception as e:
                raise self._raise_clean_http_exception(e, session, resource)

        @router.put(path, tags=[self.resource_name_plural])  # type: ignore[no-redef]
        async def organisation_image(
            identifier: str,
            file: UploadFile = File(...),
            name: str = Query(...),
            session=Depends(get_session),
            user: KeycloakUser | None = Depends(get_user_or_raise),
        ):
            self.validate_image_type(file)

            try:
                resource = self._get_resource(session, identifier)

                self._check_user_can_edit(user, resource, self.resource_name_plural)

                existing_media = next((m for m in resource.media if m.name == name), None)

                if not existing_media:
                    raise HTTPException(
                        status_code=HTTPStatus.NOT_FOUND,
                        detail=f"No image with the name '{name}' found in the database.",
                    )

                blob = await self.read_image_file(file)

                existing_media.binary_blob = blob
                existing_media.encoding_format = file.content_type
                try:
                    if hasattr(resource, "aiod_entry"):
                        resource.aiod_entry.date_modified = datetime.datetime.utcnow()
                        session.merge(resource.aiod_entry)

                    session.merge(existing_media)
                    session.commit()
                except Exception as e:
                    self._raise_clean_http_exception(e, session, resource)
                return None

            except Exception as e:
                raise self._raise_clean_http_exception(e, session, resource)

        @router.get(path, tags=[self.resource_name_plural])  # type: ignore[no-redef]
        async def organisation_image(
            identifier: str,
            session=Depends(get_session),
            user: KeycloakUser | None = Depends(get_user_or_none),
        ):
            org = session.exec(
                select(Organisation).where(Organisation.identifier == identifier)
            ).one_or_none()

            if not org:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND, detail=f"Organisation {identifier} not found."
                )

            org_image_media = []
            for media in org.media:
                if media.binary_blob:
                    media.binary_blob = base64.b64encode(media.binary_blob).decode("utf-8")
                    org_image_media.append(media)

            return org_image_media

        @router.delete(  # type: ignore[no-redef]
            path, tags=[self.resource_name_plural]
        )
        async def organisation_image(
            identifier: str,
            name: str = Query(..., description="Name of the image to delete"),
            session=Depends(get_session),
            user: KeycloakUser | None = Depends(get_user_or_raise),
        ):
            try:
                resource = session.exec(
                    select(Organisation).where(Organisation.identifier == identifier)
                ).one_or_none()

                if not resource:
                    raise HTTPException(
                        status_code=HTTPStatus.NOT_FOUND,
                        detail=f"Organisation {identifier} not found in the database.",
                    )

                if not (
                    user_can_administer(user, resource.aiod_entry)
                    or user.has_role(f"delete_{self.resource_name_plural}")
                ):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"You do not have permission to delete {self.resource_name_plural}.",
                    )

                existing_media = next((m for m in resource.media if m.name == name), None)
                if not existing_media:
                    raise HTTPException(
                        status_code=HTTPStatus.NOT_FOUND,
                        detail=f"No image with the name '{name}' found for this organisation.",
                    )

                resource.media.remove(existing_media)
                session.delete(existing_media)
                session.add(resource)
                session.commit()
                return None
            except Exception as e:
                raise as_http_exception(e)

    def create(self, url_prefix: str, version: Version = Version.LATEST) -> APIRouter:
        router = super().create(url_prefix)

        path = f"/{self.resource_name_plural}/{{identifier}}/image"
        self.add_custom_routes(router, path)

        return router

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

    def get_resource_func(self):
        """
        Return a function that can be used to retrieve a single resource.
        This function returns a function (instead of being that function directly) because the
        docstring and the variables are dynamic, and used in Swagger.
        """

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


organisation_routers = {
    version: OrganisationRouter(versioned_resource)
    for version, versioned_resource in organisation_versions.items()
}
