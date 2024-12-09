from .search_router_case_studies import SearchRouterCaseStudies
from .search_router_datasets import SearchRouterDatasets
from .search_router_educational_resources import SearchRouterEducationalResources
from .search_router_events import SearchRouterEvents
from .search_router_experiments import SearchRouterExperiments
from .search_router_ml_models import SearchRouterMLModels
from .search_router_news import SearchRouterNews
from .search_router_organisations import SearchRouterOrganisations
from .search_router_projects import SearchRouterProjects
from .search_router_publications import SearchRouterPublications
from .search_router_services import SearchRouterServices
from ..search_router import SearchRouter

router_list: list[SearchRouter] = [
    SearchRouterCaseStudies(),
    SearchRouterDatasets(),
    SearchRouterEducationalResources(),
    SearchRouterEvents(),
    SearchRouterExperiments(),
    SearchRouterMLModels(),
    SearchRouterNews(),
    SearchRouterOrganisations(),
    SearchRouterProjects(),
    SearchRouterPublications(),
    SearchRouterServices(),
]
