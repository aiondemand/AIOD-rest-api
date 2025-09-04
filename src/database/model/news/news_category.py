from typing import Type

from database.model.named_relation import create_taxonomy, Taxonomy

NewsCategory: Type[Taxonomy] = create_taxonomy(
    class_name="NewsCategory",
    table_name="news_category",
    plural_name="news categories",
)
