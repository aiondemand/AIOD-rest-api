import copy
import logging
import os
import pathlib
import tomllib
from collections import deque
from typing import Any, Sequence


# The logger isn't yet configured when we load our configuration,
# since the configuration includes our log settings. Instead, we
# keep track of what we want to log so it can be logged later.
_log_lines: deque[tuple[int, str]] = deque()
logger = logging.getLogger(__file__)

_log_lines.append((logging.INFO, f"REVIEWER_ROLE_NAME={os.getenv('REVIEWER_ROLE_NAME')}"))
_log_lines.append((logging.INFO, f"ADMIN_ROLE_NAME={os.getenv('ADMIN_ROLE_NAME')}"))

default_config_path = pathlib.Path(__file__).parent / "config.default.toml"
with open(default_config_path, "rb") as fh:
    DEFAULT_CONFIG = tomllib.load(fh)
    _log_lines.append((logging.INFO, f"Loaded default configuration from {default_config_path}"))

OVERRIDE_CONFIG_PATH = pathlib.Path(__file__).parent / "config.override.toml"
if OVERRIDE_CONFIG_PATH.exists() and OVERRIDE_CONFIG_PATH.is_file():
    with open(OVERRIDE_CONFIG_PATH, "rb") as fh:
        OVERRIDE_CONFIG = tomllib.load(fh)
        _log_lines.append(
            (logging.INFO, f"Loaded configuration overrides from {OVERRIDE_CONFIG_PATH}")
        )
else:
    OVERRIDE_CONFIG = {}
    _log_lines.append((logging.INFO, f"No custom overrides detected in {OVERRIDE_CONFIG_PATH}"))


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


def _mask_configuration(
    configuration: dict[str, Any], to_mask: Sequence[str] | None = None
) -> dict[str, Any]:
    if to_mask is None:
        to_mask = ["password"]
    masked = copy.copy(configuration)
    for key, value in configuration.items():
        if key in to_mask:
            masked[key] = "****"
        elif isinstance(value, dict):
            masked[key] = _mask_configuration(value, to_mask)
    return masked


def log_configuration():
    """Logs stacked log lines and then outputs the current configuration."""
    while _log_lines:
        level, message = _log_lines.popleft()
        logger.log(level, message)
    logger.info(f"Starting with merged configuration: {_mask_configuration(CONFIG)}")


CONFIG = _merge_configurations(DEFAULT_CONFIG, OVERRIDE_CONFIG)
DB_CONFIG = CONFIG.get("database", {})
KEYCLOAK_CONFIG = CONFIG.get("keycloak", {})
DEV_CONFIG = CONFIG.get("dev", {})
REQUEST_TIMEOUT = CONFIG.get("dev", {}).get("request_timeout", None)
