import abc
from typing import Type

from fastapi import APIRouter
from sqlalchemy.engine import Engine
from sqlmodel import select, Session

from database.model.named_relation import NamedRelation


class EnumRouter(abc.ABC):
    """
    Abstract class for FastAPI enum routers. These are routers for, for example, Language,
    making it possible to get all existing values of the Language.
    """

    def __init__(self, resource_class: Type[NamedRelation]):
        self.resource_class = resource_class
        self.resource_name = resource_class.__tablename__
        self.resource_name_plural = (
            self.resource_name + "s" if not self.resource_name.endswith("s") else self.resource_name
        )

    def create(self, engine: Engine, url_prefix: str) -> APIRouter:
        router = APIRouter()
        version = "v1"
        default_kwargs = {
            "response_model_exclude_none": True,
            "tags": ["enums"],
        }
        router.add_api_route(
            path=url_prefix + f"/{self.resource_name_plural}/{version}",
            endpoint=self.get_resources_func(engine),
            response_model=list[str],
            name=self.resource_name,
            **default_kwargs,
        )
        return router

    def get_resources_func(self, engine: Engine):
        def get_resources():
            with Session(engine) as session:
                query = select(self.resource_class)
                resources = session.scalars(query).all()
                return [r.name for r in resources]

        return get_resources

    def create_resource(self, session: Session, resource_create_instance: str):
        # Used by synchronization.py: router.create_resource
        resource = self.resource_class(name=resource_create_instance)
        session.add(resource)
        session.commit()
        return resource
