# ruff: noqa: S101  # We want early fail on startup if logging is not configured correctly
import logging
from importlib.metadata import version

from config import CONFIG, log_configuration

format_string = (
    f"v{version('aiod_metadata_catalogue')}"
    + " %(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s"
)


def setup_logger(config: dict | None = None):
    config = config or CONFIG
    assert "dev" in config, "There should be a [dev] section in the configuration.toml file."
    assert "log_level" in config["dev"], (
        "Missing `log_level` setting in the [dev] section of the configuration.toml file."
    )

    log_level: str = config["dev"]["log_level"].upper()
    levels = logging.getLevelNamesMapping()
    assert isinstance(log_level, str) and log_level in levels, (
        f"The `dev.log_level` is set to {log_level!r} but should be one of {set(levels)!r}."
    )

    logging.basicConfig(
        level=levels[log_level],
        format=format_string,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Because the configuration already had to be imported to configure logging,
    # this is the first place we can 'echo' our loaded configuration.
    log_configuration()
