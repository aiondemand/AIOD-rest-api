from database.model.dataset.dataset import Dataset
from database.model.knowledge_asset.publication import Publication
from .search_router_datasets import SearchRouterDatasets
from .search_router_publications import SearchRouterPublications
from ..search_router import SearchRouter

router_list: list[SearchRouter] = [
    SearchRouterDatasets(Dataset),
    SearchRouterPublications(Publication)
]

