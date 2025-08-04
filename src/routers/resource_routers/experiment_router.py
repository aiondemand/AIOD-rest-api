from database.model.models_and_experiments.experiment import Experiment
from routers.resource_ai_asset_router import ResourceAIAssetRouter
from versioning import Version


class ExperimentRouter(ResourceAIAssetRouter):
    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "experiment"

    @property
    def resource_name_plural(self) -> str:
        return "experiments"

    @property
    def resource_class(self) -> type[Experiment]:
        return Experiment


experiment_routers = {
    Version.V2: ExperimentRouter(),
    Version.LATEST: ExperimentRouter(),
}
