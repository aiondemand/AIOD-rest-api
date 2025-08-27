import dataclasses
from enum import StrEnum, auto
from typing import Callable, cast, TypeVar, Generic

from pydantic import create_model
from pydantic.fields import FieldInfo
from sqlmodel import SQLModel
import tomllib
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import NamedTuple

from fastapi import FastAPI
from starlette.requests import Request
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_redoc_html,
    get_swagger_ui_oauth2_redirect_html,
)
from starlette.responses import HTMLResponse

from config import CONFIG, default_config_path
from database.model.resource_read_and_create import resource_create, resource_read

logger = logging.getLogger(__file__)


class Version(StrEnum):
    V1 = auto()
    V2 = auto()
    V3 = auto()
    LATEST = auto()

    @property
    def prefix(self) -> str:
        if self == Version.LATEST:
            return ""
        return f"/{self}"


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

    if info.deprecated is not None:
        add_deprecation_header_middleware(app, date=info.deprecated, link=info.link)
        for route in app.routes:
            # Adds a visual deprecation style to the generated docs:
            route.deprecated = True

    if info.sunset is not None:
        add_sunset_header_middleware(app, date=info.sunset, link=info.link)


def add_version_to_openapi(versioned_api: FastAPI):
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
        for server in schema.get("servers", []):
            server["url"] = server["url"].removesuffix(version_prefix)
        # If everything is simply relative to the hostname, then we can drop the
        # server information, which ensures there isn't an empty dropdown menu.
        if schema.get("servers", []) == [{"url": ""}]:
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

    def overridden_swagger(request: Request):
        root_path = request.headers.get("x-forwarded-prefix", "")
        show_versions = {"latest": f"{root_path}/docs"} | {
            version: f"{root_path}/{version}/docs"
            for version, info in versions.items()
            if not info.retired
        }
        menu = generate_version_menu(all_versions=show_versions, selected=versioned_api.version)
        redirect_url = f"{root_path}{version_prefix}{versioned_api.swagger_ui_oauth2_redirect_url}"
        html_response = get_swagger_ui_html(
            openapi_url=f"{root_path}{version_prefix}/openapi.json",
            title="AI-on-Demand REST API",
            swagger_favicon_url="https://aiod.eu/wp-content/themes/aiod-v2/assets/img/favicon-192x192.png",
            oauth2_redirect_url=redirect_url,
            init_oauth=versioned_api.swagger_ui_init_oauth,
        )
        html_str = html_response.body.decode()
        start_of_swagger = html_str.find('<div id="swagger-ui">')

        new_html = (html_str[:start_of_swagger] + menu + html_str[start_of_swagger:]).encode()
        return HTMLResponse(
            content=new_html,
        )

    versioned_api.get("/docs", include_in_schema=False)(overridden_swagger)

    async def oauth_redirect(request: Request) -> HTMLResponse:
        return get_swagger_ui_oauth2_redirect_html()

    versioned_api.add_route(
        versioned_api.swagger_ui_oauth2_redirect_url, oauth_redirect, include_in_schema=False
    )

    def overridden_redoc(request: Request):
        root_path = request.headers.get("x-forwarded-prefix", "")
        html = get_redoc_html(
            openapi_url=f"{root_path}{version_prefix}/openapi.json",
            title="AI-on-Demand REST API",
            redoc_favicon_url="https://aiod.eu/wp-content/themes/aiod-v2/assets/img/favicon-192x192.png",
        )
        return html

    versioned_api.get("/redoc", include_in_schema=False)(overridden_redoc)


def generate_version_menu(all_versions: dict[str, str], selected: str) -> str:
    DARK_BLUE = "#0047BB"
    LIGHT_BLUE = "#41B6E6"
    button = '<a href={dest} style="background: {bg_color}; color: white; text-decoration: none; font-weight: bold; border-radius: 0.5em; padding: .5em 1em;">{alias}</a>'
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
    menu_div = f'<div style="display:flex; gap: 0.2em;">{"".join(buttons)}</div>'
    # Ensures the same kind of centering and other inherited properties
    return f'<div class="swagger-ui"><div class="wrapper">{menu_div}</div></div>'


class VersionMetadata(NamedTuple):
    name: str
    deprecated: datetime | None
    sunset: datetime | None
    link: str | None
    retired: bool


T = TypeVar("T")


@dataclasses.dataclass
class VersionedResource(Generic[T]):
    """
    orm_class: type[SQLModel]
        The ORM class for the resource, e.g., CaseStudy
    resource_class_create: type[SQLModel], optional
        The definition of the 'Create' interface used for `POST` and `PUT` requests.
        If not supplied, tries to create it automatically.
    resource_class_read: type[SQLModel], optional
        The definition of the 'Read' interface used for all `GET` requests.
        If not supplied, tries to create it automatically.
    create_to_orm: Callable[[SQLModel], SQLModel], optional
        A function which takes a `resource_class_create` (e.g., CaseStudyCreate),
        and produces an ORM object corresponding to the type (e.g., CaseStudy).
        If not supplied, uses the `model_validate` function from `orm_class`.
        This breaks if there is a mismatch between fields of the create class and the orm class.
    orm_to_read: Callable[[SQLModel], SQLModel], optional
        A function which takes an ORM object of the router's type (e.g., CaseStudy),
        and produces an `resource_class_read` corresponding object (e.g., CaseStudyRead).
        If not supplied, uses the `model_validate` function from `resource_read_class`.
        This breaks if there is a mismatch between fields of the read class and the orm class.
    """

    orm_class: type[T]  #: type[AIoDConcept]
    # Allow sensible defaults through None, but post_init ensures it's always set.
    resource_class_create: type[SQLModel] = None  # type: ignore[assignment]
    resource_class_read: type[SQLModel] = None  # type: ignore[assignment]
    create_to_orm: Callable[[SQLModel], T] = None  # type: ignore[assignment]
    orm_to_read: Callable[[T], SQLModel] = None  # type: ignore[assignment]

    def __post_init__(self):
        self.resource_class_create = self.resource_class_create or resource_create(self.orm_class)
        self.resource_class_read = self.resource_class_read or resource_read(self.orm_class)
        self.create_to_orm = self.create_to_orm or self.orm_class.model_validate
        self.orm_to_read = self.orm_to_read or self.resource_class_read.model_validate


def load_version_metadata(file_path: Path) -> dict[Version, VersionMetadata]:
    version_metadata = tomllib.loads(file_path.read_text())

    def _safe_date_parse(date: str | None) -> datetime | None:
        if not date:
            return None
        return datetime.strptime(date, "%Y-%m-%d").astimezone(timezone.utc)

    return {
        Version(version): VersionMetadata(
            name=version,
            deprecated=_safe_date_parse(metadata.get("deprecated")),
            sunset=_safe_date_parse(metadata.get("sunset")),
            link=metadata.get("link"),
            retired=metadata.get("retired", True),
        )
        for version, metadata in version_metadata.items()
    }


version_file = CONFIG.get("configuration", {}).get("versions")
versions = load_version_metadata(default_config_path.parent / version_file)


def schema_transform(
    original,  # : type[AIoDConcept],
    name: str,
    add_fields: dict[str, tuple[type, FieldInfo]] | None = None,
    update_fields: dict[str, tuple[type, FieldInfo]] | None = None,
    remove_fields: list[str] | None = None,
) -> type[SQLModel]:
    """Helper function for generating a modified schema based on `original`.

    Args:
        original:
          The original orm class from which the new class is to be derived.
        name:
          The name used for the new class
        add_fields:
          Dict that maps new attribute names to type annotations, e.g., {'foo': (str, Field())}
        update_fields:
          Dict that maps existing attribute names to new type annotations.
        remove_fields:
          List of fields present on `original` to remove from the new class.

    Example:
        CaseStudyV3Read = schema_transform(
            resource_read(CaseStudy),
            name="CaseStudyV3Read",
            add_fields={"foo": (str, Field(max_length=42))},
            update_fields={"bar": (int | None, Field())},
            remove_fields=["name"]
        )

    Returns:
        The generated class
    """
    add_fields = add_fields or {}
    update_fields = update_fields or {}
    remove_fields = remove_fields or []

    fields = {
        name: (model_field.annotation, model_field.field_info)
        for name, model_field in original.__fields__.items()
    }
    fields.update(add_fields | update_fields)
    new_model = create_model(name, __base__=original.__base__, **fields)
    # We need to remove the fields from the class directly, since otherwise
    # it may be inherited from the original class.
    for field in remove_fields:
        del new_model.__fields__[field]
    return new_model


class VersionedResourceCollection(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If a version is not defined, we assume no changes happened.
        # We still want this version to be accessible for general use,
        # so we map it to the next available version.
        versions = list(Version)
        latest_version = self[Version.LATEST]
        for version in reversed(versions):
            if version in self:
                latest_version = self[version]
            else:
                self[version] = latest_version
