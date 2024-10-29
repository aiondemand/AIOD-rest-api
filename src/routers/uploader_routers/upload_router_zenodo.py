from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi import File, Query, UploadFile, Path

from authentication import User, get_user_or_raise
from uploaders.zenodo_uploader import ZenodoUploader
from routers.uploader_router import UploaderRouter


class UploadRouterZenodo(UploaderRouter):
    def create(self, url_prefix: str) -> APIRouter:
        router = APIRouter()

        zenodo_uploader = ZenodoUploader()

        @router.post(url_prefix + "/upload/datasets/{identifier}/zenodo", tags=["upload"])
        def zenodo_upload(
            identifier: int = Path(
                description="The AIoD dataset identifier",
            ),
            file: UploadFile = File(
                title="File", description="This file will be uploaded to Zenodo"
            ),
            publish: Annotated[
                bool,
                Query(
                    title="Publish dataset",
                    description="Publish the dataset to Zenodo. When published, "
                    "the dataset and files will be publicly accessible "
                    "and you will no longer be able to upload more files!",
                ),
            ] = False,
            token: str = Query(title="Zenodo Token", description="The access token of Zenodo"),
            user: User = Depends(get_user_or_raise),
        ) -> int:
            """
            Use this endpoint to upload a file (content) to Zenodo using
            the AIoD metadata identifier of the dataset.

            Before uploading a dataset content, its metadata must exist on AIoD metadata catalogue
            and contain at least the following required fields:
            `name`, `description`, `creator`, `version`, and `license`.

            1. **Create Metadata**
            - If the metadata doesn't exist on AIoD catalogue, you can create it sending a `POST`
            request to `/datasets/{version}/`.
            - If the metadata already exists on zenodo, set `platform = "zenodo"` and
            `platform_resource_identifier = "zenodo.org:{id}`, where `{id}` is the identifier
            of this dataset on zenodo.
            If you don't set a value to these fields, a new repository will be create
            on Zenodo when you upload the first file on the external platform.

            2. **Upload Files**
            - Use this `POST` endpoint to upload a file to Zenodo using the AIoD metadata identifier
            of the metadata dataset.
            - Zenodo accepts multiple files for each dataset. Thus, repeat this step for each file.

            3. **Publish Dataset**
            - To make the dataset and all its content public to the AI community on Zenodo, perform
            a new `POST` request setting `publish` to `True` only when posting the last file.

            **Note:**
            - Zenodo supports multiple files within the same dataset.
            - You can replace an existing file on Zenodo by uploading another one with same name.

            """
            return zenodo_uploader.handle_upload(identifier, file, token, publish, user=user)

        return router
