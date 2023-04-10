import typing  # noqa:F401

from routers.codeartifact_router import (
    CodeArtifactRouter,
)  # noqa:F401 (flake8 raises incorrect 'Module imported but unused' error)

from .abstract_router import ResourceRouter  # noqa:F401
from .dataset_router import DatasetRouter
from .news_router import NewsRouter
from .publication_router import PublicationRouter
from .educational_resource_router import EducationalResourceRouter

routers = [
    DatasetRouter(),
    PublicationRouter(),
    NewsRouter(),
    EducationalResourceRouter(),
    CodeArtifactRouter(),
]  # type: typing.List[ResourceRouter]
