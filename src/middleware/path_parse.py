import re
from typing import Optional

from config import DEV_CONFIG
from routers.resource_routers import versioned_routers
from versioning import Version

_asset_abbreviation_to_plural = {
    r.resource_class.__abbreviation__: r.resource_name_plural
    for v in Version
    for r in versioned_routers[v]
}

ADDITIONAL_INCLUDES = {
    "assets",
    "agents",
    "ai_assets",
    "ai_resources",
}
INCLUDE = set(_asset_abbreviation_to_plural.values()) | ADDITIONAL_INCLUDES


def parse_asset_from_path(path: str) -> Optional[tuple[str, str]]:
    """If the path represents direct asset access, return the asset type and identifier.

    Direct asset access means that an asset is requested by its identifier,
    either through the resource type's router or a different one (like the generic one).
    If the path does not represent direct access, returns None.

    Examples of direct access requests:
        /v2/datasets/123           -> ("datasets", "123")
        /assets/datasets/123       -> ("datasets", "123")
        /aiod-api/v10/models/bert  -> ("models", "bert")

    Access to endpoints like `/stats`, `/metrics`, `/docs` and so on return None.
    """
    prefix = f"/{DEV_CONFIG.get('url_prefix', '')}"
    path = path.removeprefix(prefix).strip("/")

    version_match = r"v\d+"
    asset_type_match = "|".join(f"(?:{asset_type})" for asset_type in INCLUDE)
    identifier_match = "\w{3,4}_[a-zA-Z0-9]{24}"
    path_match = f"({version_match})?/?({asset_type_match})/({identifier_match})"
    if (match := re.match(path_match, path)) is None:
        return None

    version, asset_type, identifier = match.groups()
    if asset_type in ADDITIONAL_INCLUDES:
        prefix, _ = identifier.split("_")
        asset_type = _asset_abbreviation_to_plural[prefix]

    return asset_type, identifier
