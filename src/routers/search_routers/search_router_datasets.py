from database.model.dataset.dataset import Dataset
from routers.search_router import SearchRouter


class SearchRouterDatasets(SearchRouter[Dataset]):
    @property
    def es_index(self) -> str:
        return "dataset"

    @property
    def resource_name_plural(self) -> str:
        return "datasets"

    @property
    def resource_class(self):
        return Dataset

    @property
    def indexed_fields(self):
        return {"name", "description_plain", "description_html", "issn"}
