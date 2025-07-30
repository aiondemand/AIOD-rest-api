from database.model.agent.organisation import Organisation
from routers.resource_router import ResourceRouter
from fastapi import UploadFile, File, HTTPException, Query
from http import HTTPStatus
from fastapi import APIRouter, Depends
from sqlmodel import select
from database.model.agent.organisation import Organisation
from database.session import get_session
import base64
from authentication import KeycloakUser, get_user_or_none, get_user_or_raise


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp"}
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB


def validate_image_type(file: UploadFile):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type {file.content_type}. Allowed image types: {ALLOWED_IMAGE_TYPES}.",
        )


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

    def add_custom_routes(self, router: APIRouter, path: str):
        @router.post(path, tags=["organisations"])
        async def organisation_image(
            identifier: str,
            file: UploadFile = File(...),
            name: str = Query(..., description="Uploaded image filename", example="logo"),
            session=Depends(get_session),
            user: KeycloakUser | None = Depends(get_user_or_raise),
        ):
            validate_image_type(file)

            org = session.exec(
                select(Organisation).where(Organisation.identifier == identifier)
            ).one_or_none()

            if not org:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=f"Organisation {identifier} not found in the database.",
                )
            # Donot allow image upload with same name.
            # We do not check for identical image content (only name).
            # Consider adding a limit on the number of uploaded images in the future.

            existing_media = next((m for m in org.media if m.name == name), None)
            if existing_media:
                raise HTTPException(
                    status_code=HTTPStatus.CONFLICT,
                    detail=f"An image with the name '{name}' already exists for this organisation.",
                )

            blob = await file.read()

            if len(blob) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    detail="File too large (max 1MB).",
                )

            media_cls = org.__class__.media.property.mapper.class_

            media = media_cls(binary_blob=blob, name=name, encoding_format=file.content_type)
            org.media.append(media)
            session.add(media)
            session.add(org)
            session.commit()

            return {"identifier": org.identifier}

        @router.put(path, tags=["organisations"])  # type: ignore[no-redef]
        async def organisation_image(
            identifier: str,
            file: UploadFile = File(...),
            name: str = Query(...),
            session=Depends(get_session),
            user: KeycloakUser | None = Depends(get_user_or_raise),
        ):
            validate_image_type(file)

            org = session.exec(
                select(Organisation).where(Organisation.identifier == identifier)
            ).one_or_none()

            if not org:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=f"Organisation {identifier} not found in the database.",
                )

            existing_media = next((m for m in org.media if m.name == name), None)
            if not existing_media:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=f"No image with the name '{name}' found in the database.",
                )

            blob = await file.read()
            if len(blob) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    detail="File too large (max 1MB).",
                )

            existing_media.binary_blob = blob
            existing_media.encoding_format = file.content_type
            session.add(existing_media)
            session.commit()

            return None

        @router.get(path, tags=["organisations"])  # type: ignore[no-redef]
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
            path, tags=["organisations"]
        )
        async def organisation_image(
            identifier: str,
            name: str = Query(..., description="Name of the image to delete"),
            session=Depends(get_session),
            user: KeycloakUser | None = Depends(get_user_or_raise),
        ):
            org = session.exec(
                select(Organisation).where(Organisation.identifier == identifier)
            ).one_or_none()

            if not org:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=f"Organisation {identifier} not found in the database.",
                )

            existing_media = next((m for m in org.media if m.name == name), None)
            if not existing_media:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=f"No image with the name '{name}' found for this organisation.",
                )

            org.media.remove(existing_media)
            session.delete(existing_media)
            session.add(org)
            session.commit()

            return None
