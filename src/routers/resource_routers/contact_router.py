from typing import Sequence
from authentication import User
from database.model.agent.contact import Contact
from database.model.agent.email import Email
from database.model.agent.organisation import Organisation
from database.model.agent.person import Person
from database.model.platform.platform_names import PlatformName
from routers.resource_router import ResourceRouter

from sqlmodel import Session


class ContactRouter(ResourceRouter):
    def __init__(self):
        super().__init__()
        # Ugly hack to avoid "field "organisation" not yet prepared so type is still a ForwardRef"
        # error. This is caused by the circular relationship between (contact, organisation),
        # and also between (contact, person). See https://github.com/tiangolo/fastapi/issues/5607.
        Person.__init_subclass__ = lambda: None
        Organisation.__init_subclass__ = lambda: None
        for model in (self.resource_class_create, self.resource_class_read):
            model.update_forward_refs(Person=Person, Organisation=Organisation)

    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "contact"

    @property
    def resource_name_plural(self) -> str:
        return "contacts"

    @property
    def resource_class(self) -> type[Contact]:
        return Contact

    @staticmethod
    def _mask_or_filter(
        resources: Sequence[type[Contact]], session: Session, user: User | None
    ) -> Sequence[type[Contact]]:
        """
        Only authenticated users can see the contact email.
        For the old ai4europe_cms platform, only users with "full_view_ai4europe_cms_resources" role
        can view the contact emails.
        """
        for contact in resources:
            if not user or (
                (contact.platform == PlatformName.ai4europe_cms)
                and not user.has_role("full_view_ai4europe_cms_resources")
            ):
                contact.email = [Email(name="******")]
        return resources
