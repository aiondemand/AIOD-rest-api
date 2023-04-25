from typing import Type

from converters import organisation_converter_instance
from converters.abstract_converter import ResourceConverter
from database.model.organisation import OrmOrganisation
from routers.abstract_router import ResourceRouter, AIOD_CLASS, ORM_CLASS
from schemas import AIoDOrganisation


class OrganisationRouter(ResourceRouter[OrmOrganisation, AIoDOrganisation]):
    @property
    def version(self) -> int:
        return 0

    @property
    def resource_name(self) -> str:
        return "organisation"

    @property
    def resource_name_plural(self) -> str:
        return "organisations"

    @property
    def aiod_class(self) -> Type[AIOD_CLASS]:
        return AIoDOrganisation

    @property
    def orm_class(self) -> Type[ORM_CLASS]:
        return OrmOrganisation

    @property
    def converter(self) -> ResourceConverter[AIOD_CLASS, ORM_CLASS]:
        return organisation_converter_instance
