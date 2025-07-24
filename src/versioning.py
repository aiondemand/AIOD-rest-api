from datetime import datetime, timezone
import logging

from fastapi import FastAPI
from starlette.requests import Request

logger = logging.getLogger(__file__)


def add_deprecation_header_middleware(app: FastAPI, date: datetime, link: str | None = None):
    async def add_deprecation_header(request: Request, call_next):
        """Adds a deprecation header: https://datatracker.ietf.org/doc/html/rfc9745"""
        response = await call_next(request)
        response.headers["Deprecation"] = f"@{int(date.timestamp())}"
        if link is None:
            return response

        deprecation_link = f'<{link}>; rel="deprecation"; type="text/html"'
        current_link = response.headers.get("Link") or ""
        separator = ", " if current_link else ""
        response.headers["Link"] = f"{current_link}{separator}{deprecation_link}"
        return response

    app.middleware("http")(add_deprecation_header)


def add_sunset_header_middleware(app: FastAPI, date: datetime, link: str | None = None):
    async def add_sunset_header(request: Request, call_next):
        """Adds a sunset header: https://datatracker.ietf.org/doc/html/rfc8594"""
        response = await call_next(request)
        response.headers["Sunset"] = date.strftime("%a, %d %b %Y %H:%M:%S %Z")
        if link is None:
            return response

        sunset_link = f'<{link}>; rel="sunset"; type="text/html"'
        current_link = response.headers.get("Link") or ""
        separator = ", " if current_link else ""
        response.headers["Link"] = f"{current_link}{separator}{sunset_link}"
        return response

    app.middleware("http")(add_sunset_header)


def add_deprecation_and_sunset_middleware(app: FastAPI):
    info = versions.get(app.version)
    if info is None:
        logger.warning(f"Version {app.version!r} isn't present in `versions`.")
        return

    if (deprecation := info.get("deprecated")) is not None:
        add_deprecation_header_middleware(app, date=deprecation, link=info.get("link"))
        for route in app.routes:
            # Adds a visual deprecation style to the generated docs:
            route.deprecated = True

    if (sunset := info.get("sunset")) is not None:
        add_sunset_header_middleware(app, date=sunset, link=info.get("link"))


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
