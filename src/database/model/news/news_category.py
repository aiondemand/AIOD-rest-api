from database.model.named_relation import create_taxonomy

NewsCategory = create_taxonomy(class_name="NewsCategory", table_name="news_category")
