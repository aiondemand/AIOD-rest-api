import re

EXCLUDE = {
    "docs", "metrics", "openapi.json", "authorization_test",
    "counts", "favicon.ico", "health", "redoc",
}

def parse_asset_from_path(path: str) -> tuple[str, str] | None:
    """
    Normalize the path by stripping optional deployment + version prefixes.
    Return (resource_type, asset_id) or None if it's not an asset route.
    """
    segs = [s for s in path.strip("/").split("/") if s]
    if not segs:
        return None

    # deployment prefix
    if segs[0] == "aiod-api":
        segs = segs[1:]

    # version prefix v1, v2, v10, ...
    if segs and re.fullmatch(r"v\d+", segs[0]):
        segs = segs[1:]

    if len(segs) >= 2 and segs[0] not in EXCLUDE:
        return segs[0], "/".join(segs[1:])
    return None
