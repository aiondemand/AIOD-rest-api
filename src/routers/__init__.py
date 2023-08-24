import os

from elasticsearch import Elasticsearch

from .resource_router import ResourceRouter  # noqa:F401
from .resources.case_study_router import CaseStudyRouter
from .resources.computational_asset_router import ComputationalAssetRouter
from .resources.dataset_router import DatasetRouter
from .resources.educational_resource_router import EducationalResourceRouter
from .resources.event_router import EventRouter
from .resources.experiment_router import ExperimentRouter
from .resources.ml_model_router import MLModelRouter
from .resources.news_router import NewsRouter
from .resources.organisation_router import OrganisationRouter
from .resources.person_router import PersonRouter
from .resources.platform_router import PlatformRouter
from .resources.publication_router import PublicationRouter
from .resources.service_router import ServiceRouter
from .resources.team_router import TeamRouter
from .router import AIoDRouter  # noqa:F401
from .search_routers.search_router_datasets import SearchRouterDatasets
from .search_routers.search_router_publications import SearchRouterPublications
from .upload_router_huggingface import UploadRouterHuggingface

resource_routers = [
    PlatformRouter(),
    CaseStudyRouter(),
    ComputationalAssetRouter(),
    DatasetRouter(),
    EducationalResourceRouter(),
    EventRouter(),
    ExperimentRouter(),
    MLModelRouter(),
    NewsRouter(),
    OrganisationRouter(),
    PersonRouter(),
    PublicationRouter(),
    # ProjectRouter(),
    ServiceRouter(),
    TeamRouter(),
]  # type: list[ResourceRouter]


user_name = os.getenv("ES_USER")
pw = os.getenv("ES_PASSWORD")
elasticsearch_client = Elasticsearch("http://localhost:9200", basic_auth=(user_name, pw))
other_routers = [
    UploadRouterHuggingface(),
    SearchRouterDatasets(client=elasticsearch_client),
    SearchRouterPublications(client=elasticsearch_client),
]  # type: list[AIoDRouter]
