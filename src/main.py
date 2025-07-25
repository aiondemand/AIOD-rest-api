"""
Defines Rest API endpoints.

Note: order matters for overloaded paths
(https://fastapi.tiangolo.com/tutorial/path-params/#order-matters).
"""

import argparse
from datetime import datetime, timezone
import logging
from pathlib import Path

import pkg_resources
import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from sqlmodel import select, SQLModel
from starlette.requests import Request

from authentication import get_user_or_raise, KeycloakUser, assert_required_settings_configured
from config import KEYCLOAK_CONFIG, DB_CONFIG, DEV_CONFIG
from database.deletion.triggers import (
    create_delete_triggers,
    create_identifier_synchronization_triggers,
)
import database.authorization  # noqa  # Trigger registration of User, Permission -> likely obsolete when couple with aiod_entry is done
from database.model.concept.concept import AIoDConcept
from database.model.platform.platform import Platform
from database.model.platform.platform_names import PlatformName
from database.session import EngineSingleton, DbSession
from database.setup import create_database, database_exists
from taxonomies.synchronize_taxonomy import synchronize_taxonomy_from_file
from triggers import disable_review_process, enable_review_process
from error_handling import http_exception_handler
from database.model.agent.agent import Agent
from routers import (
    resource_routers,
    parent_routers,
    enum_routers,
    search_routers,
    review_router,
    user_router,
    bookmark_router,
)
from setup_logger import setup_logger


def add_routes(app: FastAPI, url_prefix=""):
    """Add routes to the FastAPI application"""

    @app.get(url_prefix + "/", response_class=HTMLResponse)
    def home() -> str:
        """Provides a redirect page to the docs."""
        return """
        <!DOCTYPE html>
        <html>
          <head>
            <meta http-equiv="refresh" content="0; url='docs'" />
          </head>
          <body>
            <p>The REST API documentation is <a href="docs">here</a>.</p>
          </body>
        </html>
        """

    for path in ["/v2/{endpoint}", "/{endpoint}"]:

        @app.get(url_prefix + path.format(endpoint="authorization_test"))
        def test_authorization(user: KeycloakUser = Depends(get_user_or_raise)) -> KeycloakUser:
            """
            Returns the user, if authenticated correctly.
            """
            return user

        @app.get(url_prefix + path.format(endpoint="counts"))
        def counts() -> dict:
            return {
                router.resource_name_plural: count
                for router in resource_routers.router_list
                if issubclass(router.resource_class, AIoDConcept)
                and (count := router.get_resource_count_func()(detailed=True))
            }

    for router in (
        resource_routers.router_list
        + parent_routers.router_list
        + enum_routers.router_list
        + search_routers.router_list
        + [review_router, user_router, bookmark_router]
    ):
        app.include_router(router.create(url_prefix))


def create_app() -> FastAPI:
    """Create the FastAPI application, complete with routes."""
    setup_logger()
    assert_required_settings_configured()
    build_database_setting = DB_CONFIG.get("build_database", "never")
    if build_database_setting == "never":
        if not database_exists():
            logging.warning(
                "AI-on-Demand database does not exist on the MySQL server, "
                "but `build_db` is set to 'never'. If you are not creating the "
                "database through other means, such as MySQL group replication, "
                "this likely means that you will get errors or undefined behavior."
            )
    else:
        drop_database = build_database_setting == "drop-then-build"
        build_database(drop_database=drop_database)

    if taxonomy_path := DEV_CONFIG.get("taxonomy"):
        if not (taxonomy_file := Path(taxonomy_path)).is_file():
            raise ValueError(f"dev.taxonomy must be a path to a file, but is {taxonomy_path!r}.")
        synchronize_taxonomy_from_file(taxonomy_file)

    pyproject_toml = pkg_resources.get_distribution("aiod_metadata_catalogue")
    app = build_app(url_prefix=DEV_CONFIG.get("url_prefix", ""), version=pyproject_toml.version)
    return app


def build_app(*, url_prefix: str = "", version: str = "dev"):
    app = FastAPI(
        openapi_url=f"{url_prefix}/openapi.json",
        docs_url=f"{url_prefix}/docs",
        title="AIoD Metadata Catalogue",
        description="This is the REST API documentation of the AIoD Metadata Catalogue. "
        "See also our general "
        '<a href="https://aiondemand.github.io/AIOD-rest-api/">metadata catalogue documentation</a>, '
        "and our "
        '<a href="https://github.com/aiondemand/AIOD-rest-api/releases">changelog</a>.',
        version=version,
        swagger_ui_oauth2_redirect_url=f"{url_prefix}/docs/oauth2-redirect",
        swagger_ui_init_oauth={
            "clientId": KEYCLOAK_CONFIG.get("client_id_swagger"),
            "realm": KEYCLOAK_CONFIG.get("realm"),
            "appName": "AIoD Metadata Catalogue",
            "usePkceWithAuthorizationCodeGrant": True,
            "scopes": KEYCLOAK_CONFIG.get("scopes"),
        },
    )
    add_routes(app, url_prefix=url_prefix)
    app.add_exception_handler(HTTPException, http_exception_handler)

    @app.middleware("http")
    async def add_deprecation_header(request: Request, call_next):
        """Adds a deprecation header: https://datatracker.ietf.org/doc/html/rfc9745"""
        response = await call_next(request)
        if "v1" in request.scope["path"]:
            deprecation_date = datetime(year=2025, month=5, day=30, tzinfo=timezone.utc)
            response.headers["Deprecation"] = f"@{int(deprecation_date.timestamp())}"
            deprecation_link = '<https://aiondemand.github.io/AIOD-rest-api/using/migration-v1-v2>; rel="deprecation"; type="text/html"'
            if links := response.headers.get("Link"):
                response.headers["Link"] = ", ".join([links, deprecation_link])
            else:
                response.headers["Link"] = deprecation_link
        return response

    @app.middleware("http")
    async def add_sunset_header(request: Request, call_next):
        """Adds a sunset header: https://datatracker.ietf.org/doc/html/rfc8594"""
        response = await call_next(request)
        if "v1" in request.scope["path"]:
            sunset_date = datetime(year=2025, month=6, day=11, tzinfo=timezone.utc)
            response.headers["Sunset"] = sunset_date.strftime("%a, %d %b %Y %H:%M:%S %Z")
            sunset_link = '<https://aiondemand.github.io/AIOD-rest-api/using/migration-v1-v2>; rel="sunset"; type="text/html"'
            if links := response.headers.get("Link"):
                response.headers["Link"] = ", ".join([links, sunset_link])
            else:
                response.headers["Link"] = sunset_link
        return response

    # Adds a visual deprecation style to the generated docs:
    for route in app.routes:
        if "v1" in route.path:
            route.deprecated = True
    return app


def build_database(drop_database: bool = False):
    create_database(delete_first=drop_database)
    SQLModel.metadata.create_all(EngineSingleton().engine, checkfirst=True)
    with DbSession() as session:
        triggers = create_delete_triggers(AIoDConcept)
        sync_triggers = create_identifier_synchronization_triggers()
        for trigger in triggers + sync_triggers:
            session.execute(trigger)

        if DEV_CONFIG.get("disable_reviews", False):
            disable_review_process(session)
        else:
            enable_review_process(session)

        existing_platforms = session.scalars(select(Platform)).all()
        missing_platforms = set(PlatformName) - {p.name for p in existing_platforms}
        if any(missing_platforms):
            session.add_all([Platform(name=name) for name in missing_platforms])
            session.commit()


def main():
    """Run the application. Placed in a separate function, to avoid having global variables"""

    # TODO: unify configuration and environment file?  GH#82
    # This parsing allows users to see the message on `--help` or incorrect (old) invocations.
    msg = (
        "Configuration options can be set in the configuration file. "
        "Please refer to the documentation pages."
    )
    argparse.ArgumentParser(description=msg).parse_args()

    uvicorn.run(
        "main:create_app",
        host="0.0.0.0",  # noqa: S104  # required to make the interface available outside of docker
        reload=DEV_CONFIG.get("reload", False),
        factory=True,
    )


if __name__ == "__main__":
    main()
