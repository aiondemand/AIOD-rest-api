from database.model.models_and_experiments.experiment import Experiment
from routers.search_router import SearchRouter


class SearchRouterExperiments(SearchRouter[Experiment]):
    @property
    def es_index(self) -> str:
        return "experiment"

    @property
    def resource_name_plural(self) -> str:
        return "experiments"

    @property
    def resource_class(self):
        return Experiment
