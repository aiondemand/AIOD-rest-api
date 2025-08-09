from database.model.named_relation import NamedRelation, Taxonomy
from routers.enum_routers.taxonomy_router import TaxonomyRouter
from routers.enum_routers.enum_router import EnumRouter
from database.model.helper_functions import non_abstract_subclasses

# Excluding some enums that should not get a router. TODO: make it configurable on the NamedRelation
__taxonomy_relations = list(
    sorted(non_abstract_subclasses(Taxonomy), key=lambda n: n.__tablename__)
)
__exclusion_list = tuple(
    ["alternate_name", "email", "note", "telephone"]
    + [n.__tablename__ for n in __taxonomy_relations]
)


__named_relations = sorted(non_abstract_subclasses(NamedRelation), key=lambda n: n.__tablename__)
__enum_relations = (n for n in __named_relations if n.__tablename__ not in __exclusion_list)

router_list: list[EnumRouter] = [EnumRouter(n) for n in __enum_relations] + [
    TaxonomyRouter(n) for n in __taxonomy_relations
]
