from datetime import datetime, timezone

from fastapi import FastAPI
from starlette.requests import Request


async def add_deprecation_header(request: Request, call_next):
    """Adds a deprecation header: https://datatracker.ietf.org/doc/html/rfc9745"""
    response = await call_next(request)
    for version, info in versions.items():
        if not request.scope["path"].startswith(f"/{version}"):
            continue
        if (deprecation_date := info.get("deprecated")) is None:
            continue
        response.headers["Deprecation"] = f"@{int(deprecation_date.timestamp())}"

        if (link := info.get("link")) is None:
            break
        deprecation_link = f'<{link}>; rel="deprecation"; type="text/html"'
        current_link = response.headers.get("Link") or ""
        separator = ", " if current_link else ""
        response.headers["Link"] = f"{current_link}{separator}{deprecation_link}"
        break
    return response


async def add_sunset_header(request: Request, call_next):
    """Adds a sunset header: https://datatracker.ietf.org/doc/html/rfc8594"""
    response = await call_next(request)
    for version, info in versions.items():
        if not request.scope["path"].startswith(f"/{version}"):
            continue
        if (sunset_date := info.get("sunset")) is None:
            continue
        response.headers["Sunset"] = sunset_date.strftime("%a, %d %b %Y %H:%M:%S %Z")

        if (link := info.get("link")) is None:
            continue
        sunset_link = f'<{link}>; rel="sunset"; type="text/html"'
        current_link = response.headers.get("Link") or ""
        separator = ", " if current_link else ""
        response.headers["Link"] = f"{current_link}{separator}{sunset_link}"
        break
    return response


def add_deprecation_and_sunset_header_data(app: FastAPI):
    app.middleware("http")(add_deprecation_header)
    app.middleware("http")(add_sunset_header)

    # Adds a visual deprecation style to the generated docs:
    for version, info in versions.items():
        if info.get("deprecated") is None:
            continue
        for route in app.routes:
            if route.path.startswith(f"/{version}"):
                route.deprecated = True


def add_version_to_openapi(versioned_api):
    """Adds the version prefix to all paths in the schema."""

    def custom_openapi():
        if versioned_api.openapi_schema:
            return versioned_api.openapi_schema
        schema = versioned_api._openapi()
        version_prefix = f"/{versioned_api.version}"

        # When the server is served under a `root_path`, this is
        # not directly available through `versioned_api.root_path`,
        # so we directly edit the generated server URLs instead.
        for server in schema["servers"]:
            server["url"] = server["url"].removesuffix(version_prefix)

        # We prefer the `/vX/...` be explicit in our documentation,
        # so that it is always obvious what documentation you are looking at.
        # Additionally, it also clearly states the entire `path`, provided that
        # the main app is not mounted to a `root_path`.
        paths = schema["paths"].copy()
        for path, metadata in paths.items():
            schema["paths"][f"{version_prefix}{path}"] = metadata
            del schema["paths"][path]

        versioned_api.openapi_schema = schema
        return schema

    versioned_api._openapi = versioned_api.openapi
    versioned_api.openapi = custom_openapi


versions: dict[str, dict] = {
    "v2": {},
    "v1": {
        "deprecated": datetime(year=2025, month=5, day=30, tzinfo=timezone.utc),
        "sunset": datetime(year=2025, month=6, day=11, tzinfo=timezone.utc),
        "link": "https://aiondemand.github.io/AIOD-rest-api/using/migration-v1-v2",
    },
}
