from fastapi import APIRouter
from fastapi import File, Query, UploadFile
from sqlalchemy.engine import Engine

from uploader.hugging_face_uploader import handle_upload


class UploadRouterHuggingface:
    def create(self, engine: Engine, url_prefix: str) -> APIRouter:
        router = APIRouter()

        @router.post(url_prefix + "/upload/datasets/{identifier}/huggingface", tags=["upload"])
        def huggingFaceUpload(
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
        ) -> int:
            return handle_upload(engine, identifier, file, token, username)

        return router
