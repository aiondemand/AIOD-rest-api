from typing import Type

from database.model.named_relation import create_taxonomy, Taxonomy

IndustrialSector: Type[Taxonomy] = create_taxonomy(
    class_name="IndustrialSector",
    table_name="industrial_sector",
    plural_name="industrial sectors",
)
