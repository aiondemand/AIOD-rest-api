from typing import TYPE_CHECKING

from database.model.concept.concept import AIoDConcept
from database.model.helper_functions import non_abstract_subclasses
from functools import cache
from versioning import Version

if TYPE_CHECKING:
    from routers import ResourceRouter


def get_all_read_classes(version: Version = Version.LATEST) -> dict[str, AIoDConcept]:
    """Returns a list of all schema types and a reference to their definition."""
    from routers.resource_routers import versioned_routers  # avoid cyclical import

    available_schemas: list[AIoDConcept] = list(non_abstract_subclasses(AIoDConcept))
    classes_dict = {clz.__tablename__: clz for clz in available_schemas if clz.__tablename__}
    resrouters = {route.resource_name: route for route in versioned_routers[version]}
    return {
        name: resrouters[name].resource_class_read
        for name in classes_dict
        if name not in ["testresource", "test_object"]
    }


def get_all_asset_schemas():
    return [
        {"$ref": f"#/components/schemas/{clz.__name__}"} for clz in get_all_read_classes().values()
    ]


@cache
def get_router_by_type() -> dict[type[AIoDConcept], type["ResourceRouter"]]:
    from routers.resource_routers import versioned_routers  # avoid cyclical import

    routers = versioned_routers[Version.LATEST]
    return {r.resource_class: r for r in routers}
