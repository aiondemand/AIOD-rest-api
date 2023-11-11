from database.model.knowledge_asset.publication import Publication
from routers.search_router import SearchRouter


class SearchRouterPublications(SearchRouter[Publication]):
    @property
    def es_index(self) -> str:
        return "publication"

    @property
    def resource_name_plural(self) -> str:
        return "publications"

    @property
    def resource_class(self):
        return Publication
    
    @property
    def match_fields(self):
        return set(['name', 'description', 'issn', 'isbn'])
