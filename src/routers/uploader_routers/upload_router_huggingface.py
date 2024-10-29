from fastapi import APIRouter, Depends
from fastapi import File, Query, UploadFile

from authentication import User, get_user_or_raise
from routers.uploader_router import UploaderRouter
from uploaders.hugging_face_uploader import HuggingfaceUploader


class UploadRouterHuggingface(UploaderRouter):
    def create(self, url_prefix: str) -> APIRouter:
        router = APIRouter()

        huggingface_uploader = HuggingfaceUploader()

        @router.post(url_prefix + "/upload/datasets/{identifier}/huggingface", tags=["upload"])
        def huggingface_upload(
            identifier: int,
            file: UploadFile = File(
                ..., title="File", description="This file will be uploaded to HuggingFace"
            ),
            token: str = Query(
                ..., title="Huggingface Token", description="The access token of HuggingFace"
            ),
            username: str = Query(
                ..., title="Huggingface username", description="The username of HuggingFace"
            ),
            user: User = Depends(get_user_or_raise),
        ) -> int:
            """
            Use this endpoint to upload a file (content) to Hugging Face using
            the AIoD metadata identifier of the dataset.

            Before uploading a dataset content, its metadata must exist on AIoD metadata catalogue.

            1. **Create Metadata**
            - If the metadata doesn't exist on AIoD catalogue, you can create it sending a `POST`
            request to `/datasets/{version}/`.
            - Make sure to set `platform = "huggingface"` and
            `platform_resource_identifier` with a string representing the repository name.

            2. **Upload File**
            - Use this `POST` endpoint to upload a file to Hugging Face using the AIoD
            metadata identifier of the metadata dataset.
            """
            return huggingface_uploader.handle_upload(identifier, file, token, username, user=user)

        return router
