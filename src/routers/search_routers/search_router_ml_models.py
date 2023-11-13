from database.model.models_and_experiments.ml_model import MLModel
from routers.search_router import SearchRouter


class SearchRouterMLModels(SearchRouter[MLModel]):
    @property
    def es_index(self) -> str:
        return "ml_model"

    @property
    def resource_name_plural(self) -> str:
        return "ml_models"

    @property
    def resource_class(self):
        return MLModel
    
    @property
    def match_fields(self):
        return set(['name', 'plain', 'html'])
