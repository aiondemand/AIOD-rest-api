import re

EXCLUDE = {
    "docs", "metrics", "openapi.json", "authorization_test",
    "counts", "favicon.ico", "health", "redoc",
}

def parse_asset_from_path(
    path: str,
    *,
    include_api_version: bool = True,
    include_resource_type_in_asset: bool = True,
) -> tuple[str, str] | None:
    """
    Parse /v2/datasets/123  -> ("datasets", "v2/datasets/123")
    Also works if there’s a deployment prefix (/aiod-api/...).

    If include_resource_type_in_asset=False you’d get ("datasets", "v2/123").
    """
    segs = [s for s in path.strip("/").split("/") if s]
    if not segs:
        return None

    # Optional deployment prefix
    if segs[0] in {"aiod-api", "aiod"}:
        segs = segs[1:]

    # Optional API version
    api_ver = None
    if segs and re.fullmatch(r"v\d+", segs[0]):
        api_ver = segs[0]
        segs = segs[1:]

    # Must be /<resource_type>/<id...>
    if len(segs) < 2 or segs[0] in EXCLUDE:
        return None

    resource_type = segs[0]
    id_tail = "/".join(segs[1:])

    parts = []
    if include_api_version and api_ver:
        parts.append(api_ver)
    if include_resource_type_in_asset:
        parts.append(resource_type)
    parts.append(id_tail)

    asset_id = "/".join(parts)
    return resource_type, asset_id
