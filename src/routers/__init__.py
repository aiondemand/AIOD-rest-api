import typing  # noqa:F401


from .abstract_router import ResourceRouter  # noqa:F401
from .dataset_router import DatasetRouter
from .news_router import NewsRouter
from .publication_router import PublicationRouter
from .educational_resource_router import EducationalResourceRouter
from .event_router import EventRouter
from .organisation_router import OrganisationRouter
from .project_router import ProjectRouter
from .codeartifact_router import CodeArtifactRouter

routers = [
    DatasetRouter(),
    PublicationRouter(),
    NewsRouter(),
    EducationalResourceRouter(),
    CodeArtifactRouter(),
    EventRouter(),
    OrganisationRouter(),
    ProjectRouter(),
]  # type: typing.List[ResourceRouter]
