from database.model.models_and_experiments.ml_model import MLModel
from routers.resource_router import ResourceRouter


class MLModelRouter(ResourceRouter):
    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "ml_model"

    @property
    def resource_name_plural(self) -> str:
        return "ml_models"

    @property
    def resource_class(self) -> type[MLModel]:
        return MLModel
