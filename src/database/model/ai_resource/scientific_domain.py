from typing import Type

from database.model.named_relation import create_taxonomy, Taxonomy

ScientificDomain: Type[Taxonomy] = create_taxonomy(
    class_name="ScientificDomain", table_name="scientific_domain"
)
