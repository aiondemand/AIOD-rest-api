from typing import Set
from routers import resource_routers     # already part of the project

def all_resource_types() -> Set[str]:
    """
    Collect the resource names each router exposes, e.g.
    {'datasets', 'models', 'case_studies', 'computational_assets', …}.
    """
    return {
        router.resource_name_plural
        for router in resource_routers.router_list
    }
