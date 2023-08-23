from database.model.dataset.dataset import Dataset

from routers.resource_router import ResourceRouter


class DatasetRouter(ResourceRouter):
    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "dataset"

    @property
    def resource_name_plural(self) -> str:
        return "datasets"

    @property
    def resource_class(self) -> type[Dataset]:
        return Dataset
