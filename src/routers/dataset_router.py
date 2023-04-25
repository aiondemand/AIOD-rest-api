from typing import Type

from converters import dataset_converter_instance
from converters.abstract_converter import ResourceConverter
from database.model.dataset import OrmDataset
from routers.abstract_router import ResourceRouter, AIOD_CLASS, ORM_CLASS
from schemas import AIoDDataset


class DatasetRouter(ResourceRouter[OrmDataset, AIoDDataset]):
    @property
    def version(self) -> int:
        return 0

    @property
    def resource_name(self) -> str:
        return "dataset"

    @property
    def resource_name_plural(self) -> str:
        return "datasets"

    @property
    def aiod_class(self) -> Type[AIOD_CLASS]:
        return AIoDDataset

    @property
    def orm_class(self) -> Type[ORM_CLASS]:
        return OrmDataset

    @property
    def converter(self) -> ResourceConverter[AIOD_CLASS, ORM_CLASS]:
        return dataset_converter_instance
