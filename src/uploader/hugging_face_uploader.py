import io
import huggingface_hub
from fastapi import HTTPException, UploadFile, status
from requests import HTTPError
from sqlalchemy.engine import Engine
from sqlalchemy.orm import joinedload
from sqlmodel import Session

from database.model.dataset.dataset import Dataset
from .utils import huggingface_license_identifiers


class HuggingfaceUploader:
    def __init__(self, engine: Engine):
        self.engine = engine

    def handle_upload(
        self,
        identifier: int,
        file: UploadFile,
        token: str,
        username: str,
    ):
        dataset = self._get_resource(engine=self.engine, identifier=identifier)
        repo_id = f"{username}/{dataset.name}"

        url = self._create_or_get_repo_url(repo_id, token)
        metadata_file = self._generate_metadata_file(dataset)
        try:
            huggingface_hub.upload_file(
                path_or_fileobj=metadata_file,
                path_in_repo="README.md",
                repo_id=repo_id,
                repo_type="dataset",
                token=token,
            )
        except HTTPError:
            msg = "Error updating the metadata, huggingface api returned a http error: {e.strerror}"
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=msg)

        except ValueError as e:
            msg = f"Error updating the metadata, bad format: {e}"
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=msg)
        except Exception:
            msg = "Error updating the metadata, unexpected error"
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=msg)

        try:
            huggingface_hub.upload_file(
                path_or_fileobj=io.BufferedReader(file.file),
                path_in_repo=f"/data/{file.filename}",
                repo_id=repo_id,
                repo_type="dataset",
                token=token,
            )
        except HTTPError as e:
            msg = f"Error uploading the file, huggingface api returned a http error: {e.strerror}"
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=msg)

        except ValueError:
            msg = "Error uploading the file, bad format"
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=msg)
        except Exception as e:
            msg = f"Error uploading the file, unexpected error: {e.with_traceback}"
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=msg)

        if not any(data.name == repo_id for data in dataset.distributions):
            self._store_resource_updated(self.engine, dataset, url, repo_id)

        return dataset.identifier

    def _get_resource(self, engine: Engine, identifier: int) -> Dataset:
        """
        Get the resource identified by AIoD identifier
        """

        with Session(engine) as session:
            query = (
                session.query(Dataset)
                .options(joinedload(Dataset.keywords), joinedload(Dataset.distributions))
                .filter(Dataset.identifier == identifier)
            )

        resource = query.first()
        if not resource:
            msg = f"Dataset '{identifier} not found in the database."
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        return resource

    def _store_resource_updated(self, engine: Engine, resource: Dataset, url: str, repo_id: str):
        raise NotImplementedError()
        # with Session(engine) as session:
        #     try:
        #         data_download = DistributionORM(content_url=url, name=repo_id, dataset=resource)
        #         resource.distributions.append(data_download)
        #         session.merge(resource)
        #         session.commit()
        #     except Exception as e:
        #         raise HTTPException(
        #             status_code=status.HTTP_502_BAD_GATEWAY,
        #             detail="Dataset metdata could not be upload",
        #         ) from e

    def _create_or_get_repo_url(sef, repo_id, token):
        try:
            url = huggingface_hub.create_repo(repo_id, repo_type="dataset", token=token)
            return url
        except Exception as e:
            if "You already created this dataset repo" in e.args[0]:
                return f"https://huggingface.co/datasets/{repo_id}"
            else:
                msg = "Error uploading the file, unexpected error"
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=msg)

    def _generate_metadata_file(self, dataset: Dataset) -> bytes:
        tags = ["- " + tag.name for tag in dataset.keywords] if dataset.keywords else []
        content = "---\n"
        content += f"pretty_name: {dataset.name}\n"

        if tags:
            content += "tags:\n"
            content += "\n".join(tags) + "\n"
        # TODO the license must be in the hugginface format:
        #  https://huggingface.co/docs/hub/repositories-licenses

        if dataset.license in huggingface_license_identifiers:
            content += f"license: {dataset.license.name if dataset.license else ''}"

        content += "---\n"
        content += f"# {dataset.name}\n"
        content += "Created from AIOD platform"  # TODO add url
        return content.encode("utf-8")
