from database.model.agent.organisation import Organisation
from routers.search_router import SearchRouter


class SearchRouterOrganisations(SearchRouter[Organisation]):
    @property
    def es_index(self) -> str:
        return "organisation"

    @property
    def resource_name_plural(self) -> str:
        return "organisations"

    @property
    def resource_class(self):
        return Organisation

    @property
    def indexed_fields(self):
        return {"name", "legal_name", "description_plain", "description_html"}
