from database.model.agent.contact import Contact
from database.model.agent.organisation import Organisation
from database.model.agent.person import Person
from routers.resource_router import ResourceRouter


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
