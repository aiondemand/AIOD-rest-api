import abc
import datetime
from typing import Any

from fastapi import HTTPException, status, UploadFile

from authentication import KeycloakUser
from database.model.dataset.dataset import Dataset
from sqlmodel import Session, select


class Uploader(abc.ABC):
    platform_name: str

    @abc.abstractmethod
    def handle_upload(
        self, identifier: int, file: UploadFile, token: str, *args: Any, user: KeycloakUser
    ) -> int:
        """Handle upload of a file to the platform and return its AIoD identifier."""

    @staticmethod
    @abc.abstractmethod
    def _platform_resource_id_validator(platform_resource_identifier: str, *args: str) -> None:
        """Throw a ValueError on an invalid platform_resource_identifier."""

    def _check_authorization(self, user: KeycloakUser) -> None:
        """
        Verifies if the user is authorised on AIoD to upload content to the external platform.
        """
        if not user.has_any_role(
            f"upload_{self.platform_name}",
            f"upload_{self.platform_name}_dataset",
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have permission to upload files to {self.platform_name}.",
            )

    def _validate_platform_name(self, name: str, identifier: int) -> None:
        """
        Validates that the provided platform name matches the expected platform name.
        """
        if name != self.platform_name:
            msg = (
                f"The dataset with identifier {identifier} should have platform="
                f"{self.platform_name}."
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    def _validate_repo_id(self, repo_id: str, *args: str) -> None:
        """
        Validates a repository ID using a custom validator function.
        """
        try:
            self._platform_resource_id_validator(repo_id, *args)
        except ValueError as e:
            msg = f"The platform_resource_identifier is invalid for {self.platform_name}. "
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg + e.args[0])

    def _get_resource(self, session: Session, identifier: int) -> Dataset:
        """
        Returns a dataset identified by its AIoD identifier.
        """
        query = select(Dataset).where(Dataset.identifier == identifier)

        dataset = session.scalars(query).first()
        if not dataset or dataset.date_deleted is not None:
            name = f"Dataset '{identifier}'"
            msg = "not found in the database"
            msg += "." if not dataset else ", because it was deleted."

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{name} {msg}")
        return dataset

    def _store_resource_updated(
        self,
        session: Session,
        resource: Dataset,
        *distribution_list: dict[str, str],
        update_all: bool = False,
    ) -> None:
        """
        Updates the resource data appending the content information as a distribution.
        """
        try:
            # Hack to get the right DistributionORM class (for each class, such as Dataset
            # and Publication, there is a different DistributionORM table).
            dist = resource.RelationshipConfig.distribution.deserializer.clazz  # type: ignore
            distribution = [dist(dataset=resource, **dist_dict) for dist_dict in distribution_list]
            if update_all:
                resource.distribution = distribution
            else:
                resource.distribution.extend(distribution)
            resource.aiod_entry.date_modified = datetime.datetime.utcnow()
            session.merge(resource)
            session.commit()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Dataset metadata could not be updated with distribution on AIoD database.",
            ) from exc
