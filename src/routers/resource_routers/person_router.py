from typing import Sequence
from sqlmodel import Session
from database.model.agent.person import Person, person_versions
from routers.resource_router import ResourceRouter
from authentication import KeycloakUser


class PersonRouter(ResourceRouter):
    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "person"

    @property
    def resource_name_plural(self) -> str:
        return "persons"

    @property
    def resource_class(self) -> type[Person]:
        return Person

    @staticmethod
    def _mask_or_filter(
        resources: Sequence[type[Person]], session: Session, user: KeycloakUser | None
    ) -> Sequence[type[Person]]:
        """
        Personal details are visible to all users.
        Email addresses are handled by the ContactRouter and are only visible to authenticated users.
        """
        return resources


person_routers = {
    version: PersonRouter(versioned_resource)
    for version, versioned_resource in person_versions.items()
}
