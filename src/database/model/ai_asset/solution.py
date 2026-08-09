from typing import Type

from database.model.named_relation import create_taxonomy, Taxonomy

Solution: Type[Taxonomy] = create_taxonomy(
    class_name="Solution",
    table_name="solution",
    plural_name="solutions",
)
