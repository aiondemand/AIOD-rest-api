from .case_study_router import CaseStudyRouter
from .computational_asset_router import ComputationalAssetRouter
from .contact_router import ContactRouter
from .dataset_router import DatasetRouter
from .educational_resource_router import EducationalResourceRouter
from .event_router import EventRouter
from .experiment_router import ExperimentRouter
from .ml_model_router import MLModelRouter
from .news_router import NewsRouter
from .organisation_router import OrganisationRouter
from .person_router import PersonRouter
from .platform_router import PlatformRouter
from .project_router import ProjectRouter
from .publication_router import PublicationRouter
from .service_router import ServiceRouter
from .team_router import TeamRouter
from .. import ResourceRouter

router_list: list[ResourceRouter] = [
    PlatformRouter(),
    CaseStudyRouter(),
    ComputationalAssetRouter(),
    ContactRouter(),
    DatasetRouter(),
    EducationalResourceRouter(),
    EventRouter(),
    ExperimentRouter(),
    MLModelRouter(),
    NewsRouter(),
    OrganisationRouter(),
    PersonRouter(),
    PublicationRouter(),
    ProjectRouter(),
    ServiceRouter(),
    TeamRouter(),
]
