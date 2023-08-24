from converters.schema.dcat import DcatApWrapper
from converters.schema.schema_dot_org import SchemaDotOrgDataset
from converters.schema_converters import (
    dataset_converter_schema_dot_org_instance,
    dataset_converter_dcatap_instance,
)
from converters.schema_converters.schema_converter import SchemaConverter
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

    @property
    def schema_converters(
        self,
    ) -> dict[str, SchemaConverter[Dataset, SchemaDotOrgDataset | DcatApWrapper]]:
        return {
            "schema.org": dataset_converter_schema_dot_org_instance,
            "dcat-ap": dataset_converter_dcatap_instance,
        }
