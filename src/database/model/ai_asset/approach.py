from typing import Type

from database.model.named_relation import create_taxonomy, Taxonomy

Approach: Type[Taxonomy] = create_taxonomy(
    class_name="Approach",
    table_name="approach",
    plural_name="approaches",
)
