import importlib.util
import json
from pathlib import Path

import warnings
from sqlalchemy.exc import SAWarning
from pydantic import BaseModel
from sqlmodel import SQLModel


def extract_relationships(model_class):
    if not hasattr(model_class, "__sqlmodel_relationships__"):
        return {}
    return {rel_name: {"name": rel_name} for rel_name in model_class.__sqlmodel_relationships__}


def extract_relationship_config_properties(model_class):
    if not hasattr(model_class, "RelationshipConfig"):
        return {}
    return {
        field_name: {
            "name": field_name,
            "type": "relationship",
            "description": getattr(field, "description", ""),
        }
        for field_name, field in vars(model_class.RelationshipConfig).items()
    }


def extract_relationship_data(model_class):
    return extract_relationships(model_class) | extract_relationship_config_properties(model_class)


def get_initial_schema(source_path: Path) -> dict:
    """
    Extracts JSON schema from Pydantic/SQLModel classes and records parent classes.
    Also adds relationships as properties.
    """
    import sys

    sys.path.append(str(source_path.absolute()))

    all_schemas = {}
    read_error = {}
    class_parents = {}
    for path in (source_path / "database" / "model").rglob("*"):
        if path.suffix != ".py" or path.stem.startswith("__"):
            continue

        try:
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message=".*This declarative base already contains.*",
                    category=SAWarning,
                )
                warnings.filterwarnings(
                    "ignore",
                    message=".*fields may not start with an underscore,.*",
                    category=RuntimeWarning,
                )
                spec = importlib.util.spec_from_file_location(path.stem, path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

            for attr_name in dir(module):
                if attr_name == "Location":
                    continue  # Ignoring Location since `schema_json` errors
                SQLModel.metadata.clear()
                attr = getattr(module, attr_name)
                # Only process Pydantic/SQLModel classes
                if not (
                    isinstance(attr, type)
                    and issubclass(attr, BaseModel)
                    and attr not in [BaseModel, SQLModel]
                ):
                    continue

                schema = attr.schema_json()
                schema_dict = json.loads(schema)

                # Add relationships to properties
                schema_dict.setdefault("properties", {}).update(extract_relationship_data(attr))

                # Store schema
                all_schemas[attr.__name__] = schema_dict

                # Get parent classes dynamically
                parent_classes = [
                    parent.__name__
                    for parent in attr.__bases__
                    if isinstance(parent, type)
                    and issubclass(parent, BaseModel)
                    and parent is not BaseModel
                ]

                # Store parent mapping
                class_parents[attr.__name__] = parent_classes

        except Exception as e:
            read_error.update({path.stem: e})

    return all_schemas, read_error, class_parents
