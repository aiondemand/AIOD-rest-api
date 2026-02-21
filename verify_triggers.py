import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd() / "src"))

from database.deletion.triggers import create_deletion_trigger_many_to_many
from database.model.dataset.dataset import Dataset
from database.model.ai_resource.keyword import Keyword
from database.model.helper_functions import many_to_many_link_factory

# Mock many-to-many relationship details
link_model = many_to_many_link_factory("dataset", "keyword", from_identifier_type=str)
other_links = ["model_keyword_link", "publication_keyword_link"]

ddl = create_deletion_trigger_many_to_many(
    trigger=Dataset,
    link=link_model,
    to_delete=Keyword,
    other_links=other_links
)

print("-" * 20)
print("Generated DDL:")
print(ddl.statement)
print("-" * 20)
