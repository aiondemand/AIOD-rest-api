from typing import Type

from database.model.named_relation import create_taxonomy, Taxonomy

License: Type[Taxonomy] = create_taxonomy(class_name="License", table_name="license")
