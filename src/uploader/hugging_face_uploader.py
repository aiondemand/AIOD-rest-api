import io

import huggingface_hub
from fastapi import HTTPException, UploadFile, status
from requests import HTTPError
from sqlmodel import Session

from database.model.dataset.dataset import Dataset
from database.session import DbSession
from .utils import huggingface_license_identifiers


def handle_upload(
    identifier: int,
    file: UploadFile,
    token: str,
    username: str,
):
    with DbSession() as session:
        dataset = _get_resource(session=session, identifier=identifier)
        dataset_name_cleaned = "".join(c if c.isalnum() else "_" for c in dataset.name)
        repo_id = f"{username}/{dataset_name_cleaned}"

        url = _create_or_get_repo_url(repo_id, token)
        metadata_file = _generate_metadata_file(dataset)
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

        if not any(data.name == repo_id for data in dataset.distribution):
            _store_resource_updated(session, dataset, url, repo_id)

        return dataset.identifier


def _get_resource(session: Session, identifier: int) -> Dataset:
    """
    Get the resource identified by AIoD identifier
    """

    query = session.query(Dataset).filter(Dataset.identifier == identifier)

    resource = query.first()
    if not resource:
        msg = f"Dataset '{identifier} not found in the database."
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
    return resource


def _store_resource_updated(session: Session, resource: Dataset, url: str, repo_id: str):
    try:
        # Hack to get the right DistributionORM class (for each class, such as Dataset
        # and Publication, there is a different DistributionORM table).
        dist = resource.RelationshipConfig.distribution.deserializer.clazz  # type: ignore
        distribution = dist(content_url=url, name=repo_id, dataset=resource)
        resource.distribution.append(distribution)
        session.merge(resource)
        session.commit()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Dataset metadata could not be uploaded",
        ) from e


def _create_or_get_repo_url(repo_id, token):
    try:
        url = huggingface_hub.create_repo(repo_id, repo_type="dataset", token=token)
        return url
    except Exception as e:
        if "You already created this dataset repo" in e.args[0]:
            return f"https://huggingface.co/datasets/{repo_id}"
        else:
            msg = "Error uploading the file, unexpected error"
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=msg) from e


def _generate_metadata_file(dataset: Dataset) -> bytes:
    tags = ["- " + tag.name for tag in dataset.keyword] if dataset.keyword else []
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
