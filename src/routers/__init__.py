import os

from elasticsearch import Elasticsearch

from routers.resource_router import ResourceRouter  # noqa:F401
from routers.resources.case_study_router import CaseStudyRouter
from routers.resources.computational_asset_router import ComputationalAssetRouter
from routers.resources.dataset_router import DatasetRouter
from routers.resources.educational_resource_router import EducationalResourceRouter
from routers.resources.experiment_router import ExperimentRouter
from routers.resources.ml_model_router import MLModelRouter
from routers.resources.organisation_router import OrganisationRouter
from routers.resources.person_router import PersonRouter
from routers.resources.platform_router import PlatformRouter
from routers.resources.publication_router import PublicationRouter
from routers.resources.service_router import ServiceRouter
from routers.resources.team_router import TeamRouter
from routers.router import AIoDRouter  # noqa:F401
from routers.search_router import SearchRouter  # noqa:F401
from routers.search_routers.search_router_datasets import SearchRouterDatasets
from routers.search_routers.search_router_publications import SearchRouterPublications
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


user_name = os.getenv("ES_USER")
pw = os.getenv("ES_PASSWORD")
elasticsearch_client = Elasticsearch("http://localhost:9200", basic_auth=(user_name, pw))
other_routers = [
    UploadRouterHuggingface(),
    SearchRouterDatasets(client=elasticsearch_client),
    SearchRouterPublications(client=elasticsearch_client),
]  # type: list[AIoDRouter]
