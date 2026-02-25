import dataclasses
import json
import argparse
from pathlib import Path


from schema_inspector import get_initial_schema

IGNORES = []

# Some classes are implemented under a different name
# Implementation: Conceptual Model
class_maps = {
    "News": "News Item",
    "IndustrialSector": "Business Sector",
    "Turnover": "Company Revenue",
    "NumberOfEmployees": "Company Size",
    "AIoDEntryRead": "AIoD Entry",
}

# All names in this maps should be normalized
# Class: {Implementation: Conceptual Model}
property_renames_by_class = {
    "aiodentry": {"datecreated": "entrycreated", "datemodified": "modified"},
    "airesource": {
        "alternatename": "alternativename",
        "industrialsector": "businesssector",
        "ispartof": "partof",
    },
    "computationalasset": {"type": "computationalassettype"},
    "educationalresource": {
        "prerequisite": "prerequisiteknowledge",
        "targetaudience": "targetseducationallevel",
    },
    "event": {
        "status": "currenteventstatus",
        "mode": "usesmode",
    },
    "experiment": {"executionsettings": "exemplaryexecutionsettings"},
    "publication": {
        "isbn": "hasisbn",
        "issn": "hasissn",
    },
    "person": {"languages": "language"},
    "aiasset": {"license": "licence"},
    "runnabledistribution": {"deploymenttimemilliseconds": "deploymenttimemsec"},
}
# Some classes are artefacts of the implementation or are required for
# other parts of the system. We can ignore them in this comparison.
class_ignores = {
    # Classes defined for convenience to help with the conceptual model implementation
    "Taxonomy",
    "NamedRelation",
    "Text",
    "Body",
    # Classes defined for the REST API unrelated to the conceptual model
    "Bookmark",
    "AIoDEntryCreate",
}

property_suffix_ignores = {"_id", "_identifier", "__"}


def normalize(string: str) -> str:
    return string.casefold().replace(" ", "").replace("_", "")


def main():
    parser = argparse.ArgumentParser(
        description="Compare implementation schema with conceptual model definition."
    )
    parser.add_argument(
        "source_path",
        type=str,
        help="Path to the implementation source directory",
    )
    parser.add_argument(
        "conceptual_model_path",
        type=str,
        help="Path to the model export definition file",
    )
    parser.add_argument(
        "--class",
        "-c",
        dest="class_name",
        type=str,
        help="Optional: Name of a specific class to inspect (as defined in the model)",
    )

    args = parser.parse_args()

    source_path = Path(args.source_path)
    if not (source_path.exists() and source_path.is_dir()):
        parser.error(f"No source directory {source_path.absolute()} found.")

    conceptual_model_path = Path(args.conceptual_model_path)
    if not (conceptual_model_path.exists() and conceptual_model_path.is_file()):
        parser.error(f"No conceptual model file {conceptual_model_path.absolute()} found.")

    implementation = load_implemented_schema(source_path)
    definition = json.loads(conceptual_model_path.read_text())
    conceptual_model = {clazz["name"]: clazz for clazz in definition["classes"]}

    report_differences(implementation, conceptual_model, args.class_name)


def load_implemented_schema(source_path) -> dict:
    implemented_classes, errors, class_hierarchy = get_initial_schema(source_path)
    for clazz, metadata in implemented_classes.items():
        metadata["parents"] = {}
        parents = class_hierarchy.get(clazz, [])[:]
        while parents:
            parent = parents.pop()
            if parent in ["SQLModel", "BaseModel"]:
                continue
            metadata["parents"][parent] = implemented_classes[parent]
            parents.extend(class_hierarchy.get(parent, []))

        all_properties = dict(metadata["properties"].items())
        inherited_properties = {
            name: property
            for parent_name, parent in metadata["parents"].items()
            for name, property in parent["properties"].items()
            # If the name matches with a Base suffix, it should be considered as a direct definition
            # The structure of the code base has ItemBase defining properties which will be properties  # noqa: E501
            # of the table in the database, and Item defines the relationships to other tables.
            if parent_name != f"{clazz}Base"
        }
        metadata["inherited_properties"] = inherited_properties
        metadata["direct_properties"] = {
            k: v for k, v in all_properties.items() if k not in inherited_properties
        }

    implemented_classes = {
        class_maps.get(k, k): v
        for k, v in implemented_classes.items()
        if not any(k.endswith(suffix) for suffix in ["Base", "ORM", "Table", "Link"])
        and k not in class_ignores
    }
    return implemented_classes


def report_differences(implementation: dict, definition: dict, class_name=None):
    names_implementation = {normalize(name): name for name in implementation}
    names_definition = {normalize(name): name for name in definition}

    matching = sorted(set(names_implementation) & set(names_definition))
    only_implementation = sorted(set(names_implementation) - set(names_definition))
    only_definition = sorted(set(names_definition) - set(names_implementation))

    if class_name:
        matching = set(matching) & {normalize(class_name)}
        only_implementation = set(only_implementation) & {normalize(class_name)}
        only_definition = set(only_definition) & {normalize(class_name)}
        if not (matching | only_definition | only_implementation):
            return

    for clazz in matching:
        impl = implementation[names_implementation[clazz]]
        if "Taxonomy" in impl["parents"]:
            continue

        diffs = report_difference(
            implementation[names_implementation[clazz]], definition[names_definition[clazz]], clazz
        )
        if diffs:
            [dataclasses.asdict(d) for d in diffs]


@dataclasses.dataclass
class Comparison:
    normalized_name: str
    defined_as: str | None = None
    implemented_as: str | None = None
    defined_type: str | None = None
    implemented_type: str | None = None


def report_difference(implementation: dict, definition: dict, clazz: str) -> list[Comparison]:
    implemented_properties = {
        normalize(prop): prop
        for prop in implementation["direct_properties"]
        if not any(prop.endswith(suffix) for suffix in property_suffix_ignores)
    }
    defined_properties = {normalize(prop["name"]): prop for prop in definition["direct_properties"]}

    all_properties = set(defined_properties) | set(implemented_properties)
    property_renames = property_renames_by_class.get(clazz, {})
    # To avoid reporting a property twice, we only pick one of two definitions for properties
    # which are named differently in implementation than the conceptual model.
    all_properties = {p for p in all_properties if p not in property_renames.values()}

    property_map = []
    for property_name in all_properties:
        prop = Comparison(normalized_name=property_name)
        if implemented_as := implemented_properties.get(property_name):
            prop.implemented_as = implemented_as
            prop.implemented_type = implementation["properties"][implemented_as].get(
                "type", "TYPE_UNKNOWN"
            )

        if different_name := property_renames.get(property_name):
            property_name = different_name
        if defined_as := defined_properties.get(property_name):
            prop.defined_as = defined_as["name"]
            def_type = defined_as["range"]
            if isinstance(def_type, list) and len(def_type) == 1:
                def_type = def_type[0]
            prop.defined_type = def_type
        property_map.append(prop)

    def sort_properties(comparison):
        # we want the matched properties, then unmatched properties
        if comparison.implemented_as and comparison.defined_as:
            return ord(comparison.defined_as[0])
        if comparison.defined_as:
            return ord(comparison.defined_as[0]) + 26
        if comparison.implemented_as:
            return ord(comparison.implemented_as[0]) + 26 * 2
        raise NotImplementedError

    return sorted(property_map, key=sort_properties)


if __name__ == "__main__":
    main()
