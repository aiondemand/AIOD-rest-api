#!python3
"""See README.md of the metadata-model-comparison directory"""

import dataclasses
import json
import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

PATH_ROOT = Path(__file__).parent.parent
PATH_DEMOKRITOS = PATH_ROOT / "data" / "aiod-model-demokritos.json"
PATH_IMPLEMENTED = PATH_ROOT / "data" / "implemented.json"

PATH_RESULT = PATH_ROOT / "output"
PATH_RESULT_COMPLETE = PATH_RESULT / "complete.csv"
PATH_RESULT_DATASET = PATH_RESULT / "dataset.csv"
PATH_RESULT_PERSON = PATH_RESULT / "person.csv"
PATH_RESULT_NON_ABSTRACT = PATH_RESULT / "non_abstract.csv"


EXCLUDE_DEMOKRITOS = {"AIResource", "AIoDConcept", "AIAsset", "Knowledgeasset", "Agent"}
EXCLUDE_IMPLEMENTED = {
    "Body_",
    "SchemaDotOrg",
    "Error",
    "VCard",
    "Dcat",
    "Dct",
    "XSD",
    "Create",
    "Spdx",
    "User",
}
ABSTRACT_PROPERTIES_IMPL = {
    "ai_asset_identifier",
    "ai_resource_identifier",
    "aiod_entry",
    "application_area",
    "is_accessible_for_free",
    "media",
    "note",
    "platform",
    "platform_resource_identifier",
    "relevant_link",
    "relevant_resource",
    "relevant_to",
}


RE_SNAKE_CASE = re.compile(r"([A-Z]+)")


def snake_case(string: str) -> str:
    return RE_SNAKE_CASE.sub(r"_\1", string).lower()


@dataclasses.dataclass
class Property:
    type: str
    name: str
    description: str
    required: bool
    array: bool
    defined_on: str | None
    extra: str | None

    @classmethod
    def from_demokritos(cls, p: dict[str, Any], defined_on: str):
        """
        "name": "identifier",
        "type": "URL",
        "cardinality": "1",
        "source": "aiod",
        "description": ""
        """
        return cls(
            p["type"] if p["type"] else None,
            snake_case(p["name"]),
            p["description"] if p["description"] else None,
            p["cardinality"] == "1",
            p["cardinality"] in ("n*", "0*"),
            defined_on,
            None,
        )

    @classmethod
    def from_implementation(cls, name: str, p: dict[str, Any], required: bool):
        """
         "platform": {
          "type": "string",
          "maxLength": 64,
          "title": "Platform",
          "description": "The external platform from which this resource ...",
          "example": "example"
        },
        """
        is_array = False
        if "allOf" in p:
            type_ = p["allOf"]
        elif "$ref" in p:
            type_ = p["$ref"]
        else:
            if (type_ := p["type"]) == "array":
                is_array = True
                type_ = p["items"]["type"] if "type" in p["items"] else p["items"]["$ref"]
        if isinstance(type_, list):
            type_ = type_[0]["$ref"]
            is_array = True
        return cls(
            type_,
            name,
            p.get("description", None),
            required,
            is_array,
            None,
            ", ".join(
                f"{key}: {value}"
                for key, value in p.items()
                if key not in ("type", "title", "description")
            ),
        )


@dataclasses.dataclass
class Entity:
    name: str
    properties: list[Property]

    @classmethod
    def from_demokritos(cls, entity: dict[str, Any], schema_dict_d: dict[str, Any]):
        if any(exclusion in entity["name"] for exclusion in EXCLUDE_DEMOKRITOS):
            return
        properties = [Property.from_demokritos(p, entity["name"]) for p in entity["properties"]]
        schema = entity
        while parent := schema.get("parent", None):
            schema = schema_dict_d[parent.lower()]
            properties.extend(Property.from_demokritos(p, parent) for p in schema["properties"])
        return cls(entity["name"], properties)

    @classmethod
    def from_implementation(cls, name: str, schema: dict[str, Any]):
        if any(exclusion in name for exclusion in EXCLUDE_IMPLEMENTED):
            return
        if name.endswith("Read"):
            name = name[:-4]
        required = set(schema["required"] if "required" in schema else [])
        properties = [
            prop
            for p_name, p in schema["properties"].items()
            if (prop := (Property.from_implementation(p_name, p, p_name in required)))
        ]
        return cls(name, properties)


def to_dataframe(entities: list[Entity]) -> pd.DataFrame:
    df = pd.DataFrame(
        [
            {"entity_name": entity.name} | prop.__dict__
            for entity in entities
            for prop in entity.properties
        ]
    )
    return df.set_index(["entity_name", "name"])


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    if not PATH_IMPLEMENTED.exists():
        logging.error(
            "Download the last implemented json first. You can do so with the "
            "download_implemented_fields.sh script"
        )
        exit(1)
    with PATH_DEMOKRITOS.open("r") as f:
        demokritos = json.load(f)
    with PATH_IMPLEMENTED.open("r") as f:
        implemented = json.load(f)

    schema_dict_d = {schema["name"].lower(): schema for schema in demokritos["entities"]}
    entities_d = [
        entity
        for schema in demokritos["entities"]
        if (entity := Entity.from_demokritos(schema, schema_dict_d))
    ]
    entities_i = [
        entity
        for name, schema in implemented["components"]["schemas"].items()
        if (entity := Entity.from_implementation(name, schema))
    ]
    df_d = to_dataframe(entities_d)
    df_i = to_dataframe(entities_i)
    df = (
        df_d.join(df_i, how="outer", lsuffix="_dmkr", rsuffix="_impl")
        .rename(columns={"defined_on_dmkr": "defined_on"})
        .drop(columns=["defined_on_impl", "extra_dmkr"])
        .reset_index()
        .reindex(
            [
                "entity_name",
                "defined_on",
                "name",
                "comments",
                "type_dmkr",
                "type_impl",
                "array_dmkr",
                "array_impl",
                "required_dmkr",
                "required_impl",
                "description_dmkr",
                "description_impl",
                "extra_impl",
            ],
            axis=1,
        )
        .sort_values(["entity_name", "defined_on", "name"])
    )

    PATH_RESULT.mkdir(exist_ok=True)
    logging.info(f"Writing all fields to {PATH_RESULT_COMPLETE}")
    df.to_csv(PATH_RESULT_COMPLETE, index=False)
    logging.info(f"Writing non abstract fields to {PATH_RESULT_NON_ABSTRACT}")
    df[
        (pd.isnull(df["defined_on"]) | (df["entity_name"] == df["defined_on"]))
        & (~df["name"].isin(ABSTRACT_PROPERTIES_IMPL))
    ].to_csv(PATH_RESULT_NON_ABSTRACT, index=False)

    logging.info(f"Writing Dataset (with all abstract fields) to  {PATH_RESULT_DATASET}")
    df[df["entity_name"] == "Dataset"].to_csv(PATH_RESULT_DATASET, index=False)
    logging.info(f"Writing Person (with all abstract fields) to  {PATH_RESULT_DATASET}")
    df[df["entity_name"] == "Person"].to_csv(PATH_RESULT_PERSON, index=False)
    logging.info(f"Done")


if __name__ == "__main__":
    main()
