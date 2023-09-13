import os
from elasticsearch import Elasticsearch

from database.model.dataset.dataset import Dataset
from database.model.models_and_experiments.experiment import Experiment
from database.model.models_and_experiments.ml_model import MLModel
from database.model.knowledge_asset.publication import Publication
from database.model.service.service import Service
from .search_router_datasets import SearchRouterDatasets
from .search_router_experiments import SearchRouterExperiments
from .search_router_ml_models import SearchRouterMLModels
from .search_router_publications import SearchRouterPublications
from .search_router_services import SearchRouterServices
from ..search_router import SearchRouter

# Elasticsearch client
user = os.getenv("ES_USER")
pw = os.getenv("ES_PASSWORD")
es_client = Elasticsearch("http://elasticsearch:9200", basic_auth=(user, pw))

router_list: list[SearchRouter] = [
    SearchRouterDatasets(client=es_client),
    SearchRouterExperiments(client=es_client),
    SearchRouterMLModels(client=es_client),
    SearchRouterPublications(client=es_client),
    SearchRouterServices(client=es_client)
]
