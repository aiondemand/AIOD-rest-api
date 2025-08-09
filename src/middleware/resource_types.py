from typing import Set
from routers import (
    resource_routers,
    parent_routers,
    uploader_routers,
)


def all_resource_types() -> Set[str]:
    """
    Gather every plural resource name exposed by *any* router group,
    e.g. {'datasets', 'ml_models', 'computational_assets', …}.
    Uses getattr guard so it doesn’t crash when a router lacks the attribute.
    """
    router_lists = resource_routers.router_list
    types: Set[str] = set()
    for router in router_lists:
        val = getattr(router, "resource_name_plural", None)
        if val:
            types.add(val)
    return types
