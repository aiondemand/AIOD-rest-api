from routers.resources.dataset_router import DatasetRouter
from routers.resources.experiment_router import ExperimentRouter
from routers.resources.ml_model_router import MLModelRouter
from routers.resources.organisation_router import OrganisationRouter
from routers.resources.person_router import PersonRouter
from routers.resources.platform_router import PlatformRouter
from routers.resources.publication_router import PublicationRouter
from .resource_router import ResourceRouter  # noqa:F401
from routers.resources.service_router import ServiceRouter
from .router import AIoDRouter  # noqa:F401
from .search_router import SearchRouter
from .upload_router_huggingface import UploadRouterHuggingface

resource_routers = [
    PlatformRouter(),
    # CaseStudyRouter(),
    # ComputationalResourceRouter(),
    DatasetRouter(),
    # EducationalResourceRouter(),
    # EventRouter(),
    ExperimentRouter(),
    MLModelRouter(),
    # NewsRouter(),
    OrganisationRouter(),
    PersonRouter(),
    PublicationRouter(),
    # ProjectRouter(),
    # PresentationRouter(),
    ServiceRouter(),
]  # type: list[ResourceRouter]

other_routers = [UploadRouterHuggingface(), SearchRouter()]  # type: list[AIoDRouter]
