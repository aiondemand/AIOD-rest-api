from database.model.named_relation import create_taxonomy

PublicationType = create_taxonomy(class_name="PublicationType", table_name="publication_type")
