from database.model.agent.organisation import Organisation
from routers.resource_router import ResourceRouter
from fastapi import UploadFile, File, HTTPException
from fastapi import APIRouter, Depends
from sqlmodel import select
from database.model.agent.organisation import Organisation
from starlette.status import HTTP_404_NOT_FOUND, HTTP_413_REQUEST_ENTITY_TOO_LARGE
from database.session import get_session


class OrganisationRouter(ResourceRouter):
    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "organisation"

    @property
    def resource_name_plural(self) -> str:
        return "organisations"

    @property
    def resource_class(self) -> type[Organisation]:
        return Organisation
