import os
from elasticsearch import Elasticsearch

from .search_router_datasets import SearchRouterDatasets
from .search_router_events import SearchRouterEvents
from .search_router_experiments import SearchRouterExperiments
from .search_router_ml_models import SearchRouterMLModels
from .search_router_news import SearchRouterNews
from .search_router_organisations import SearchRouterOrganisations
from .search_router_projects import SearchRouterProjects
from .search_router_publications import SearchRouterPublications
from .search_router_services import SearchRouterServices
from ..search_router import SearchRouter

# Elasticsearch client
user = os.getenv("ES_USER")
pw = os.getenv("ES_PASSWORD")
es_client = Elasticsearch("http://elasticsearch:9200", basic_auth=(user, pw))

router_list: list[SearchRouter] = [
    SearchRouterDatasets(client=es_client),
    SearchRouterEvents(client=es_client),
    SearchRouterExperiments(client=es_client),
    SearchRouterMLModels(client=es_client),
    SearchRouterNews(client=es_client),
    SearchRouterOrganisations(client=es_client),
    SearchRouterProjects(client=es_client),
    SearchRouterPublications(client=es_client),
    SearchRouterServices(client=es_client)
]
