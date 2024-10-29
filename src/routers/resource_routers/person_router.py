from typing import Sequence
from sqlmodel import Session
from database.model.agent.person import Person
from database.model.platform.platform_names import PlatformName
from routers.resource_router import ResourceRouter
from authentication import User


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
        resources: Sequence[type[Person]], session: Session, user: User | None
    ) -> Sequence[type[Person]]:
        """
        For the old ai4europe_cms platform, only users with "full_view_ai4europe_cms_resources"
        role can see the person's sensitive information.
        """
        for person in resources:
            if (person.platform == PlatformName.ai4europe_cms) and not (
                user and user.has_role("full_view_ai4europe_cms_resources")
            ):
                person.name = "******"
                person.given_name = "******"
                person.surname = "******"
        return resources
