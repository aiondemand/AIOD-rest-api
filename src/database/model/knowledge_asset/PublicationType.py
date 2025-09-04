from typing import Type

from database.model.named_relation import create_taxonomy, Taxonomy

PublicationType: Type[Taxonomy] = create_taxonomy(
    class_name="PublicationType",
    table_name="publication_type",
    plural_name="publication types",
)
