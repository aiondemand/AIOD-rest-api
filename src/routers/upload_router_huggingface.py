from fastapi import APIRouter
from fastapi import File, Query, UploadFile
from sqlalchemy.engine import Engine

from routers.router import AIoDRouter
from uploader.hugging_face_uploader import HuggingfaceUploader


class UploadRouterHuggingface(AIoDRouter):
    def create(self, engine: Engine, url_prefix: str) -> APIRouter:
        router = APIRouter()
        uploader = HuggingfaceUploader(engine)

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
            return uploader.handle_upload(identifier, file, token, username)

        return router
