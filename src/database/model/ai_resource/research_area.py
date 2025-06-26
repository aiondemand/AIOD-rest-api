from typing import Type

from database.model.named_relation import create_taxonomy, Taxonomy

ResearchArea: Type[Taxonomy] = create_taxonomy(
    class_name="ResearchArea", table_name="research_area"
)
