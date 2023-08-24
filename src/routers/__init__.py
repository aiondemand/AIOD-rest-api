from routers.case_study_router import CaseStudyRouter
from routers.computational_asset_router import ComputationalAssetRouter
from routers.educational_resource_router import EducationalResourceRouter
from routers.resource_router import ResourceRouter  # noqa:F401
from routers.resources.dataset_router import DatasetRouter
from routers.resources.experiment_router import ExperimentRouter
from routers.resources.ml_model_router import MLModelRouter
from routers.resources.organisation_router import OrganisationRouter
from routers.resources.person_router import PersonRouter
from routers.resources.platform_router import PlatformRouter
from routers.resources.publication_router import PublicationRouter
from routers.resources.service_router import ServiceRouter
from routers.router import AIoDRouter  # noqa:F401
from routers.search_router import SearchRouter
from routers.team_router import TeamRouter
from routers.upload_router_huggingface import UploadRouterHuggingface


resource_routers = [
    PlatformRouter(),
    CaseStudyRouter(),
    ComputationalAssetRouter(),
    DatasetRouter(),
    EducationalResourceRouter(),
    # EventRouter(),
    ExperimentRouter(),
    MLModelRouter(),
    # NewsRouter(),
    OrganisationRouter(),
    PersonRouter(),
    PublicationRouter(),
    # ProjectRouter(),
    ServiceRouter(),
    TeamRouter(),
]  # type: list[ResourceRouter]

other_routers = [UploadRouterHuggingface(), SearchRouter()]  # type: list[AIoDRouter]
