from database.model.agent.organisation import Organisation
from routers.resource_router import ResourceRouter
from fastapi import UploadFile, File, HTTPException, Query
from http import HTTPStatus
from fastapi import APIRouter, Depends
from sqlmodel import select
from database.model.agent.organisation import Organisation
from database.session import get_session


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

    def add_custom_routes(self, router: APIRouter, url_prefix: str):
        @router.post(
            f"{url_prefix}/organisations/{{identifier}}/upload-image", tags=["organisations"]
        )
        async def upload_organisation_logo(
            identifier: str,
            file: UploadFile = File(...),
            name: str = Query(..., description="Uploaded image filename", example="logo"),
            session=Depends(get_session),
        ):
            org = session.exec(
                select(Organisation).where(Organisation.identifier == identifier)
            ).one_or_none()

            if not org:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=f"Organisation {identifier} not found in the database.",
                )
            # Donot allow image upload with same name.
            # However, we deliberately donot check if same image is being uploaded.
            # At some point we should introduce limit on no of image uploaded.
            existing_media = next((m for m in org.media if m.name == name), None)
            if existing_media:
                raise HTTPException(
                    status_code=HTTPStatus.CONFLICT,
                    detail=f"An image with the name '{name}' already exists for this organisation.",
                )

            blob = await file.read()

            if len(blob) > 1 * 1024 * 1024:
                raise HTTPException(
                    status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    detail="File too large (max 1MB)",
                )

            media_cls = org.__class__.media.property.mapper.class_

            media = media_cls(image_blob=blob, name=name, encoding_format=file.content_type)
            org.media.append(media)
            session.add(media)
            session.add(org)
            session.commit()

            return {"identifier": org.identifier}

        @router.put("/organisations/{identifier}/update-image", tags=["organisations"])
        async def update_organisation_logo(
            identifier: str,
            file: UploadFile = File(...),
            name: str = Query(...),
            session=Depends(get_session),
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
                    detail=f"No image with the name '{name}' found in the database.",
                )

            blob = await file.read()
            if len(blob) > 1 * 1024 * 1024:
                raise HTTPException(
                    status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    detail="File too large (max 1MB)",
                )

            existing_media.image_blob = blob
            existing_media.encoding_format = file.content_type
            session.add(existing_media)
            session.commit()

            return None

        @router.delete(
            f"{url_prefix}/organisations/{{identifier}}/delete-image", tags=["organisations"]
        )
        async def delete_organisation_logo(
            identifier: str,
            name: str = Query(..., description="Name of the image to delete"),
            session=Depends(get_session),
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
