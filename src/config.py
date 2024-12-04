import copy
import pathlib
import tomllib
from typing import Any

with open(pathlib.Path(__file__).parent / "config.default.toml", "rb") as fh:
    DEFAULT_CONFIG = tomllib.load(fh)

OVERRIDE_CONFIG_PATH = pathlib.Path(__file__).parent / "config.override.toml"
if OVERRIDE_CONFIG_PATH.exists() and OVERRIDE_CONFIG_PATH.is_file():
    with open(OVERRIDE_CONFIG_PATH, "rb") as fh:
        OVERRIDE_CONFIG = tomllib.load(fh)
else:
    OVERRIDE_CONFIG = {}


def _merge_configurations(
    default: dict[str, Any], override: dict[str, Any], path: str = "root"
) -> dict[str, Any]:
    if extra_keys := (set(override) - set(default)):
        keys = ", ".join(map(repr, extra_keys))
        raise KeyError(f"The custom configuration has unknown key(s) at {path!r}: {keys}")
    merged = copy.copy(default)
    for key, value in override.items():
        if isinstance(value, dict):
            merged[key] = _merge_configurations(default[key], value, path=f"{path}.{key}")
        else:
            merged[key] = value
    return merged


CONFIG = _merge_configurations(DEFAULT_CONFIG, OVERRIDE_CONFIG)
DB_CONFIG = CONFIG.get("database", {})
KEYCLOAK_CONFIG = CONFIG.get("keycloak", {})
REQUEST_TIMEOUT = CONFIG.get("dev", {}).get("request_timeout", None)
