import io
import json
import requests

from datetime import datetime
from typing import Optional

from fastapi import UploadFile, HTTPException, status

from authentication import User
from config import REQUEST_TIMEOUT

from database.model.agent.contact import Contact
from database.model.ai_asset.license import License
from database.model.ai_resource.text import TextORM
from database.model.concept.status import Status
from database.model.dataset.dataset import Dataset
from database.model.platform.platform_names import PlatformName
from database.session import DbSession
from database.validators import zenodo_validators

from error_handling import as_http_exception
from uploaders.uploader import Uploader


class ZenodoUploader(Uploader):
    BASE_URL = "https://zenodo.org/api/deposit/depositions"

    def __init__(self) -> None:
        self.platform_name = PlatformName.zenodo

    def handle_upload(
        self, identifier: int, file: UploadFile, token: str, *args: bool, user: User
    ) -> int:
        """
        Method to upload content to the Zenodo platform.
        """
        self._check_authorization(user)

        publish = args[0]
        with DbSession() as session:
            dataset = self._get_resource(session, identifier)
            metadata = self._generate_metadata(dataset, publish)

            dataset.platform = dataset.platform or PlatformName.zenodo
            self._validate_platform_name(dataset.platform, identifier)

            platform_resource_id = dataset.platform_resource_identifier
            if platform_resource_id is None:
                zenodo_metadata = self._create_repo(metadata, token)

                repo_id = zenodo_metadata["id"]
                platform_resource_id = f"zenodo.org:{repo_id}"
                self._validate_repo_id(platform_resource_id)
                dataset.platform_resource_identifier = platform_resource_id
            else:
                self._validate_repo_id(platform_resource_id)
                repo_id = platform_resource_id.split(":")[-1]
                zenodo_metadata = self._get_metadata_from_zenodo(repo_id, token)

                if dataset.aiod_entry.status and dataset.aiod_entry.status.name == "published":
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=(
                            "This resource is already public and can't be edited with this "
                            "endpoint. You can access and modify it at "
                            f"{zenodo_metadata['links']['html']}",
                        ),
                    )
                self._update_zenodo_metadata(metadata, repo_id, token)

            repo_url = zenodo_metadata["links"]["bucket"]
            self._upload_file(repo_url, file, token)

            if publish:
                new_zenodo_metadata = self._publish_resource(repo_id, token)
                record_url = new_zenodo_metadata["links"]["record"]
                distribution = self._get_distribution(repo_id, token, record_url)

                new_status = session.query(Status).filter(
                    Status.name == "published"
                ).first() or Status(name="published")
                dataset.aiod_entry.status = new_status
                dataset.date_published = datetime.utcnow()
            else:
                distribution = self._get_distribution(repo_id, token)

            self._store_resource_updated(session, dataset, *distribution, update_all=True)

            return dataset.identifier

    @staticmethod
    def _platform_resource_id_validator(platform_resource_identifier: str, *args) -> None:
        return zenodo_validators.throw_error_on_invalid_identifier(platform_resource_identifier)

    def _generate_metadata(self, dataset: Dataset, publish: bool) -> dict:
        """
        Generates metadata as a dictionary based on the data from the dataset model.
        """

        if not dataset.name:
            msg = "A 'name' of the dataset is required."
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

        if not dataset.version:
            msg = (
                "A version of the dataset is required. Any string is accepted, however "
                "the suggested format is a semantically versioned tag (more details at semver.org)."
            )
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
            "access_right": "open" if dataset.is_accessible_for_free else "closed",
            "license": license_id,
        }
        return metadata

    def _create_repo(self, metadata: dict, token: str) -> dict:
        """
        Creates an empty repo with some metadata on Zenodo.
        """
        params = {"access_token": token}
        try:
            res = requests.post(
                self.BASE_URL,
                params=params,
                json={"metadata": metadata},
                timeout=REQUEST_TIMEOUT,
            )
        except Exception as exc:
            raise as_http_exception(exc)

        if res.status_code != status.HTTP_201_CREATED:
            msg = "Failed to create a new repo on Zenodo."
            _wrap_bad_gateway_error(res, msg)

        return res.json()

    def _get_metadata_from_zenodo(self, repo_id: str, token: str) -> dict:
        """
        Get metadata of the dataset identified by its identifier `repo_id` from Zenodo.
        """
        params = {"access_token": token}
        try:
            res = requests.get(f"{self.BASE_URL}/{repo_id}", params=params, timeout=REQUEST_TIMEOUT)
        except Exception as exc:
            raise as_http_exception(exc)

        if res.status_code != status.HTTP_200_OK:
            msg = "Failed to retrieve information from Zenodo."
            _wrap_bad_gateway_error(res, msg)

        return res.json()

    def _update_zenodo_metadata(self, metadata: dict, repo_id: str, token: str) -> None:
        """
        Updates the zenodo repo with some metadata.
        """
        headers = {"Content-Type": "application/json"}
        try:
            res = requests.put(
                f"{self.BASE_URL}/{repo_id}",
                params={"access_token": token},
                data=json.dumps({"metadata": metadata}),
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
        except Exception as exc:
            raise as_http_exception(exc)

        if res.status_code != status.HTTP_200_OK:
            msg = "Failed to upload metadata to Zenodo."
            _wrap_bad_gateway_error(res, msg)

    def _upload_file(self, repo_url: str, file: UploadFile, token: str) -> None:
        """
        Uploads a file to zenodo using a bucket url where the files are stored.
        """
        params = {"access_token": token}
        try:
            res = requests.put(
                f"{repo_url}/{file.filename}",
                data=io.BufferedReader(file.file),
                params=params,
                timeout=REQUEST_TIMEOUT,
            )
        except Exception as exc:
            raise as_http_exception(exc)

        if res.status_code != status.HTTP_201_CREATED:
            msg = "Failed to upload the file to zenodo."
            _wrap_bad_gateway_error(res, msg)

    def _publish_resource(self, repo_id: str, token: str) -> dict:
        """
        Publishes the dataset with all content on Zenodo.
        """
        params = {"access_token": token}
        try:
            res = requests.post(
                f"{self.BASE_URL}/{repo_id}/actions/publish", params=params, timeout=REQUEST_TIMEOUT
            )
        except Exception as exc:
            raise as_http_exception(exc)

        if res.status_code != status.HTTP_202_ACCEPTED:
            msg = "Failed to publish the dataset on zenodo."
            _wrap_bad_gateway_error(res, msg)

        return res.json()

    def _get_distribution(
        self, repo_id: str, token: str, public_url: str | None = None
    ) -> list[dict]:
        """
        Gets metadata of the published files.
        """
        params = None if public_url else {"access_token": token}
        url = public_url or f"{self.BASE_URL}/{repo_id}"

        try:
            res = requests.get(f"{url}/files", params=params, timeout=REQUEST_TIMEOUT)
        except Exception as exc:
            raise as_http_exception(exc)

        if res.status_code != status.HTTP_200_OK:
            msg = (
                f"Failed to retrieve the resource files {'' if public_url else 'in draft'} "
                "from zenodo."
            )
            _wrap_bad_gateway_error(res, msg)

        files_metadata = res.json()["entries"] if public_url else res.json()
        distribution = [
            {
                "platform": PlatformName.zenodo,
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

    def _get_and_validate_license(self, license_: License | None) -> str:
        """
        Checks if the provided license is valid for uploading content to Zenodo.
        """
        try:
            res = requests.get(
                "https://zenodo.org/api/vocabularies/licenses?q=&tags=data", timeout=REQUEST_TIMEOUT
            )
        except Exception as exc:
            raise as_http_exception(exc)
        if res.status_code != status.HTTP_200_OK:
            msg = "Failed to get the list of valid licenses to upload content on Zenodo."
            _wrap_bad_gateway_error(res, msg)

        valid_license_ids: list[str] = [item["id"] for item in res.json()["hits"]["hits"]]
        if (license_ is None) or (license_.name not in valid_license_ids):
            msg = (
                "License must be one of the following license identifiers allowed "
                "to upload data on Zenodo: " + ", ".join(valid_license_ids) + ". "
                "For details, refer to Zenodo API documentation: "
                "https://developers.zenodo.org/#licenses."
            )
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)

        return license_.name

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
                "The dataset must have the name of at least one creator. "
                "Please provide either the person's given name and surname "
                "or the organization name. If given name and surname are not provided, "
                "the API will attempt to retrieve the name from the fields person.name, "
                "organization.name, and contact.name, in this order."
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

        return creator_names


def _wrap_bad_gateway_error(response: requests.Response, msg: str):
    res_json = response.json()
    res_msg = res_json.get("message", "")
    msg_to_append = str(response.status_code) + (f" - {res_msg}" if res_msg else "")
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"{msg} Zenodo returned an error or an unexpected status code: {msg_to_append}",
    )
