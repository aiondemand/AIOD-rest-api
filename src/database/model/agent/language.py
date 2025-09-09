from database.model.named_relation import create_taxonomy

Language = create_taxonomy(
    class_name="Language",
    table_name="language",
    plural_name="languages",
)
