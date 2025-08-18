from database.model.models_and_experiments.ml_model import MLModel, ml_model_versions
from routers.resource_ai_asset_router import ResourceAIAssetRouter


class MLModelRouter(ResourceAIAssetRouter):
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


ml_model_routers = {
    version: MLModelRouter(versioned_resource)
    for version, versioned_resource in ml_model_versions.items()
}
