import routers
from database.model.concept.concept import AIoDConcept
from database.model.helper_functions import non_abstract_subclasses


def get_all_asset_schemas():
    available_schemas: list[AIoDConcept] = list(non_abstract_subclasses(AIoDConcept))
    classes_dict = {clz.__tablename__: clz for clz in available_schemas if clz.__tablename__}
    resrouters = {
        route.resource_name: route
        for route in routers.resource_routers.router_list  # type: ignore
    }
    read_classes_dict = {
        name: resrouters[name].resource_class_read
        for name in classes_dict
        if name not in ["testresource", "test_object"]
    }
    responses = [
        {"$ref": f"#/components/schemas/{clz.__name__}"} for clz in read_classes_dict.values()
    ]
    return responses
