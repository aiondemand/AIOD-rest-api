import abc

from fastapi import APIRouter
from sqlalchemy.engine import Engine


class AIoDRouter(abc.ABC):
    @abc.abstractmethod
    def create(self, engine: Engine, url_prefix: str) -> APIRouter:
        pass
