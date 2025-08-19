import re
from typing import Optional, Tuple

EXCLUDE = {
    "docs",
    "metrics",
    "openapi.json",
    "authorization_test",
    "counts",
    "favicon.ico",
    "health",
    "redoc",
}


def _strip_deployment_and_api_version(segs: list[str]) -> tuple[Optional[str], list[str]]:
    """
    Removes optional deployment prefix ('aiod-api' or 'aiod') and a leading API version 'v<digits>'.
    Returns (api_version_if_any, remaining_segments).
    """
    if segs and segs[0] in {"aiod-api", "aiod"}:
        segs = segs[1:]
    api_ver = None
    if segs and re.fullmatch(r"v\d+", segs[0]):
        api_ver = segs[0]
        segs = segs[1:]
    return api_ver, segs


def _split_identifier_prefix(identifier: str) -> Tuple[str, str]:
    """
    Supports both:
      - slash form: 'datasets/123' -> ('datasets', '123')
      - colon form: 'models:bert'  -> ('models',   'bert')
    Returns (resource_type, tail_without_type).
    """
    if ":" in identifier and "/" not in identifier:
        rtype, tail = identifier.split(":", 1)
        return rtype, tail
    parts = identifier.split("/")
    rtype = parts[0]
    tail = "/".join(parts[1:]) if len(parts) > 1 else ""
    return rtype, tail


def parse_asset_from_path(
    path: str,
    *,
    include_api_version: bool = False,
    include_resource_type_in_asset: bool = False,
) -> Optional[tuple[str, str]]:
    """
    Parse an incoming request path into (resource_type, asset_id).

    - Understands:
        /v2/datasets/123           -> ("datasets", "123")      [with defaults]
        /datasets/v1/1             -> ("datasets", "v1/1")
        /assets/datasets/123       -> ("datasets", "123")
        /assets/models:bert        -> ("models", "bert")
        /aiod-api/v10/models/bert  -> ("models", "bert")

    - EXCLUDE set is ignored (docs, metrics, etc.)
    """
    segs = [s for s in path.strip("/").split("/") if s]
    if not segs:
        return None

    _, segs = _strip_deployment_and_api_version(segs)

    if not segs or segs[0] in EXCLUDE:
        return None

    if segs[0] == "assets":
        if len(segs) < 2:
            return None
        identifier = "/".join(segs[1:])
        rtype, tail = _split_identifier_prefix(identifier)
        asset_id = f"{rtype}/{tail}" if include_resource_type_in_asset else tail
        return rtype, asset_id

    if len(segs) >= 2:
        rtype = segs[0]
        tail = "/".join(segs[1:])
        asset_id = f"{rtype}/{tail}" if include_resource_type_in_asset else tail
        return rtype, asset_id

    return None
