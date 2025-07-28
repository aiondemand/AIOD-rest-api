from datetime import datetime, timezone
import logging

from fastapi import FastAPI
from starlette.requests import Request
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from starlette.responses import HTMLResponse

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


def add_version_to_openapi(versioned_api: FastAPI, root_path: str = ""):
    """Adds the version prefix to all paths in the schema."""
    if versioned_api.version == "latest":
        version_prefix = ""
    else:
        version_prefix = f"/{versioned_api.version}"

    def custom_openapi():
        if versioned_api.openapi_schema:
            return versioned_api.openapi_schema
        schema = versioned_api._openapi()

        # We edit the servers instead of dropping them to preserve information
        # on the root_path and hostname.
        for server in schema["servers"]:
            server["url"] = server["url"].removesuffix(version_prefix)
        # If everything is simply relative to the hostname, then we can drop the
        # server information, which ensures there isn't an empty dropdown menu.
        if schema["servers"] == [{"url": ""}]:
            del schema["servers"]

        versioned_api.openapi_schema = schema
        if not version_prefix:
            return schema

        # We prefer the `/vX/...` be explicit in our documentation,
        # so that it is always obvious what documentation you are looking at.
        # Additionally, it also clearly states the entire `path`, provided that
        # the main app is not mounted to a `root_path`.
        paths = schema["paths"].copy()
        for path, metadata in paths.items():
            schema["paths"][f"{version_prefix}{path}"] = metadata
            del schema["paths"][path]
        return schema

    versioned_api._openapi = versioned_api.openapi
    versioned_api.openapi = custom_openapi

    def overridden_swagger():
        html_response = get_swagger_ui_html(
            openapi_url=f"{root_path}{version_prefix}/openapi.json",
            title="AI-on-Demand REST API",
            swagger_favicon_url="https://aiod.eu/wp-content/themes/aiod-v2/assets/img/favicon-192x192.png",
        )
        html_str = html_response.body.decode()
        start_of_swagger = html_str.find('<div id="swagger-ui">')
        menu = generate_version_menu(
            dict(v2=f"{root_path}/v2/docs", v1=f"{root_path}/v1/docs", latest=f"{root_path}/docs"),
            selected=versioned_api.version,
        )
        new_html = (html_str[:start_of_swagger] + menu + html_str[start_of_swagger:]).encode()
        return HTMLResponse(
            content=new_html,
        )

    versioned_api.get("/docs", include_in_schema=False)(overridden_swagger)

    def overridden_redoc():
        html = get_redoc_html(
            openapi_url="/openapi.json",
            title="AI-on-Demand REST API",
            redoc_favicon_url="https://aiod.eu/wp-content/themes/aiod-v2/assets/img/favicon-192x192.png",
        )
        return html

    versioned_api.get("/redoc", include_in_schema=False)(overridden_redoc)


def generate_version_menu(all_versions: dict[str, str], selected: str) -> str:
    DARK_BLUE = "#0047BB"
    LIGHT_BLUE = "#41B6E6"
    button = '<a href={dest} style="background: {bg_color}; color: white; text-decoration: none; font-weight: bold; border-radius: 0.5em; padding: 10px 5px;">{alias}</a>'
    buttons = []
    for name, url in all_versions.items():
        bg_color = LIGHT_BLUE if name == selected else DARK_BLUE
        buttons.append(
            button.format(
                dest=url,
                bg_color=bg_color,
                alias=name,
            )
        )
    menu_div = "".join(buttons)
    return f'<div class="swagger-ui"><div class="wrapper">{menu_div}</div></div>'


versions: dict[str, dict] = {
    "v2": {},
    "v1": {
        "deprecated": datetime(year=2025, month=5, day=30, tzinfo=timezone.utc),
        "sunset": datetime(year=2025, month=6, day=11, tzinfo=timezone.utc),
        "link": "https://aiondemand.github.io/AIOD-rest-api/using/migration-v1-v2",
        "retired": True,
    },
}
