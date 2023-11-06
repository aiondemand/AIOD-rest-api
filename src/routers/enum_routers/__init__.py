from database.model.named_relation import NamedRelation
from routers.enum_routers.enum_router import EnumRouter
from database.model.helper_functions import non_abstract_subclasses

# Excluding some enums that should not get a router. TODO: make it configurable on the NamedRelation
__exclusion_list = ("alternate_name", "email", "note", "telephone")


__named_relations = sorted(non_abstract_subclasses(NamedRelation), key=lambda n: n.__tablename__)
__filtered_relations = (n for n in __named_relations if n.__tablename__ not in __exclusion_list)

router_list: list[EnumRouter] = [EnumRouter(n) for n in __filtered_relations]
