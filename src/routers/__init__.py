from .resource_router import ResourceRouter  # noqa:F401
from .upload_router_huggingface import UploadRouterHuggingface

from .search_routers.search_router_datasets import SearchRouterDatasets
from .search_routers.search_router_experiments import SearchRouterExperiments
from .search_routers.search_router_ml_models import SearchRouterMLModels
from .search_routers.search_router_publications import SearchRouterPublications

import os
from elasticsearch import Elasticsearch


user_name = os.getenv("ES_USER")
pw = os.getenv("ES_PASSWORD")

elasticsearch_client = Elasticsearch("http://localhost:9200", basic_auth=(user_name, pw))

other_routers = [
    UploadRouterHuggingface(),
    SearchRouterDatasets(client=elasticsearch_client),
    SearchRouterExperiments(client=elasticsearch_client),
    SearchRouterMLModels(client=elasticsearch_client),
    SearchRouterPublications(client=elasticsearch_client),
]
