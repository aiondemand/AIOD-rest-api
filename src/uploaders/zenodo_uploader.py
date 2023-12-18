from datetime import datetime
import io
import json
from typing import Optional
import requests

from fastapi import UploadFile, HTTPException, status
from database.model.agent.contact import Contact
from database.model.ai_asset.license import License
from database.model.ai_resource.text import TextORM

from database.model.concept.status import Status
from database.model.dataset.dataset import Dataset
from database.model.platform.platform_names import PlatformName

from database.session import DbSession
from database.validators import zenodo_validators
from error_handlers import _wrap_as_http_exception
from uploaders.uploader import Uploader


class ZenodoUploader(Uploader):
    BASE_URL = "https://zenodo.org/api/deposit/depositions"

    def __init__(self) -> None:
        super().__init__(PlatformName.zenodo, zenodo_validators.throw_error_on_invalid_identifier)

    def handle_upload(self, identifier: int, publish: bool, token: str, file: UploadFile):
        """
        Method to upload content to the Zenodo platform.
        """
        self.token = token
        with DbSession() as session:
            dataset = self._get_resource(session, identifier)
            platform_resource_id = dataset.platform_resource_identifier
            platform_name = dataset.platform

            self._validate_patform_name(platform_name, identifier)
            self._validate_repo_id(platform_resource_id)

            metadata = self._generate_metadata(dataset, publish)

            if platform_resource_id is None:
                zenodo_metadata = self._create_repo(metadata)
                self.repo_id = zenodo_metadata["id"]
                dataset.platform = "zenodo"
                dataset.platform_resource_identifier = f"zenodo.org:{self.repo_id}"
            else:
                self.repo_id = platform_resource_id.split(":")[-1]
                zenodo_metadata = self._get_metadata_from_zenodo()

                if dataset.aiod_entry.status and dataset.aiod_entry.status.name == "published":
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=(
                            "This resource is already public and can't be edited with this "
                            "endpoint. You can access and modify it at "
                            f"{zenodo_metadata['links']['record']}",
                        ),
                    )
                self._update_zenodo_metadata(metadata)

            repo_url = zenodo_metadata["links"]["bucket"]
            self._upload_file(repo_url, file)

            if publish:
                new_zenodo_metadata = self._publish_resource()
                record_url = new_zenodo_metadata["links"]["record"]
                distribution = self._get_distribution(record_url)

                new_status = session.query(Status).filter(
                    Status.name == "published"
                ).first() or Status(name="published")
                dataset.aiod_entry.status = new_status
                dataset.date_published = datetime.utcnow()
            else:
                distribution = self._get_distribution()

            self._store_resource_updated(session, dataset, *distribution, update_all=True)

            return dataset.identifier

    def _generate_metadata(self, dataset: Dataset, publish: bool) -> dict:
        """
        Generates metadata as a dictionary based on the data from the dataset model.
        """

        if not dataset.name:
            msg = "A 'name' of the dataset is required."
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

        if publish and not (dataset.is_accessible_for_free):
            msg = (
                "To publish the dataset on zenodo, you must set the field "
                "'is_accessible_for_free' as `True`"
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

        description = self._get_and_validate_description(dataset.description)
        creator_names = self._get_and_validate_creators(dataset.creator, publish)
        license_id = self._get_and_validate_license(dataset.license)

        metadata = {
            "title": dataset.name,
            "version": dataset.version,
            "description": description,
            "upload_type": "dataset",
            "creators": creator_names,
            "keywords": [kw.name for kw in dataset.keyword],
            "method": dataset.measurement_technique,
            "access_right": f"{'open' if dataset.is_accessible_for_free else 'closed'}",
            "license": license_id,
        }
        return metadata

    def _create_repo(self, metadata: dict) -> dict:
        """
        Creates an empty repo with some metadata on Zenodo.
        """
        params = {"access_token": self.token}
        try:
            res = requests.post(
                self.BASE_URL,
                params=params,
                json={"metadata": metadata},
            )
        except Exception as exc:
            raise _wrap_as_http_exception(exc)

        if res.status_code != status.HTTP_201_CREATED:
            msg = "Failed to create a new repo on Zenodo."
            _wrap_bad_gateway_error(msg, res.status_code)

        return res.json()

    def _get_metadata_from_zenodo(self) -> dict:
        """
        Get metadata of the dataset identified by its identifier `repo_id` from Zenodo.
        """
        params = {"access_token": self.token}
        try:
            res = requests.get(f"{self.BASE_URL}/{self.repo_id}", params=params)
        except Exception as exc:
            raise _wrap_as_http_exception(exc)

        if res.status_code != status.HTTP_200_OK:
            msg = "Failed to retrieve information from Zenodo."
            _wrap_bad_gateway_error(msg, res.status_code)

        return res.json()

    def _update_zenodo_metadata(self, metadata: dict) -> None:
        """
        Updates the zenodo repo with some metadata.
        """
        headers = {"Content-Type": "application/json"}
        try:
            res = requests.put(
                f"{self.BASE_URL}/{self.repo_id}",
                params={"access_token": self.token},
                data=json.dumps({"metadata": metadata}),
                headers=headers,
            )
        except Exception as exc:
            raise _wrap_as_http_exception(exc)

        if res.status_code != status.HTTP_200_OK:
            msg = "Failed to upload metadata to Zenodo."
            _wrap_bad_gateway_error(msg, res.status_code)

    def _upload_file(self, repo_url: str, file: UploadFile) -> None:
        """
        Uploads a file to zenodo using a bucket url where the files are stored.
        """
        params = {"access_token": self.token}
        try:
            res = requests.put(
                f"{repo_url}/{file.filename}", data=io.BufferedReader(file.file), params=params
            )
        except Exception as exc:
            raise _wrap_as_http_exception(exc)

        if res.status_code != status.HTTP_201_CREATED:
            msg = "Failed to upload the file to zenodo."
            _wrap_bad_gateway_error(msg, res.status_code)

    def _publish_resource(self) -> dict:
        """
        Publishes the dataset with all content on Zenodo.
        """
        params = {"access_token": self.token}
        try:
            res = requests.post(f"{self.BASE_URL}/{self.repo_id}/actions/publish", params=params)
        except Exception as exc:
            raise _wrap_as_http_exception(exc)

        if res.status_code != status.HTTP_202_ACCEPTED:
            msg = "Failed to publish the dataset on zenodo."
            _wrap_bad_gateway_error(msg, res.status_code)

        return res.json()

    def _get_distribution(self, public_url: str | None = None) -> list[dict]:
        """
        Gets metadata of the published files.
        """
        params = None if public_url else {"access_token": self.token}
        url = public_url or f"{self.BASE_URL}/{self.repo_id}"

        try:
            res = requests.get(f"{url}/files", params=params)
        except Exception as exc:
            raise _wrap_as_http_exception(exc)

        if res.status_code != status.HTTP_200_OK:
            msg = (
                f"Failed to retrieve the resource files {'' if public_url else 'in draft'} "
                "from zenodo."
            )
            _wrap_bad_gateway_error(msg, res.status_code)

        files_metadata = res.json()["entries"] if public_url else res.json()
        distribution = [
            {
                "platform": "zenodo",
                "platform_resource_identifier": file["file_id" if public_url else "id"],
                "checksum": file["checksum"].split(":")[-1] if public_url else file["checksum"],
                "checksum_algorithm": "md5",
                "content_url": file["links"]["content" if public_url else "download"],
                "content_size_kb": round(file["size" if public_url else "filesize"] / 1000),
                "name": file["key" if public_url else "filename"],
            }
            for file in files_metadata
        ]

        return distribution

    def _get_and_validate_license(self, license: License | None) -> str:
        """
        Checks if the provided license is valid for uploading content to Zenodo.
        """
        try:
            res = requests.get("https://zenodo.org/api/vocabularies/licenses?q=&tags=data")
        except Exception as exc:
            raise _wrap_as_http_exception(exc)
        if res.status_code != status.HTTP_200_OK:
            msg = "Failed to get the list of valid licenses to upload content on Zenodo."
            _wrap_bad_gateway_error(msg, res.status_code)

        valid_license_ids: list[str] = [item["id"] for item in res.json()["hits"]["hits"]]
        if (license is None) or (license.name not in valid_license_ids):
            msg = (
                "License must be one of the following license identifiers allowed "
                "to upload data on Zenodo: " + ", ".join(valid_license_ids) + ". "
                "For details, refer to Zenodo API documentation: "
                "https://developers.zenodo.org/#licenses."
            )
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)

        return license.name

    def _get_and_validate_description(self, description: TextORM | None) -> str:
        if description and description.html:
            desc = description.html + "<p><strong>Created from AIOD platform.</strong></p>"
        elif description and description.plain:
            desc = description.plain + "\nCreated from AIOD platform."

        else:
            msg = "Provide a description for this dataset, either as html or as plain text."
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

        return desc

    def _get_and_validate_creators(
        self, creators: list[Contact], publish: bool
    ) -> list[Optional[dict[str, str]]]:
        creator_names: list[Optional[dict[str, str]]] = []
        for contact in creators:
            if contact.person and contact.person.given_name and contact.person.surname:
                name: str | None = ", ".join([contact.person.surname, contact.person.given_name])
            elif contact.person and contact.person.name:
                name = contact.person.name
            elif contact.organisation and contact.organisation.name:
                name = contact.organisation.name
            else:
                name = contact.name
            if name:
                creator_names.append({"name": name})

        if publish and (not creator_names):
            msg = (
                "The dataset must have the name of at least one contact. "
                "Please provide either the person's given name and surname "
                "or the organization name. If given name and surname are not provided, "
                "the API will attempt to retrieve the name from the fields person.name, "
                "organization.name, and contact.name, in this order."
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

        return creator_names


def _wrap_bad_gateway_error(msg: str, status_code: int):
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"{msg} Zenodo returned a http error with status code: {status_code}.",
    )