"""
Defines Rest API endpoints.

Note: order matters for overloaded paths
(https://fastapi.tiangolo.com/tutorial/path-params/#order-matters).
"""

import argparse
import logging

import pkg_resources
import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from sqlmodel import select, SQLModel

from authentication import get_user_or_raise, KeycloakUser, assert_required_settings_configured
from config import KEYCLOAK_CONFIG
from database.deletion.triggers import create_delete_triggers
import database.authorization  # noqa  # Trigger registration of User, Permission -> likely obsolete when couple with aiod_entry is done
from database.model.concept.concept import AIoDConcept
from database.model.platform.platform import Platform
from database.model.platform.platform_names import PlatformName
from database.session import EngineSingleton, DbSession
from database.setup import create_database, database_exists
from error_handling import http_exception_handler
from routers import (
    resource_routers,
    parent_routers,
    enum_routers,
    uploader_routers,
    search_routers,
    review_router,
    user_router,
)
from setup_logger import setup_logger


def _parse_args() -> argparse.Namespace:
    # TODO: refactor configuration (https://github.com/aiondemand/AIOD-rest-api/issues/82)
    parser = argparse.ArgumentParser(description="Please refer to the README.")
    parser.add_argument("--url-prefix", default="", help="Prefix for the api url.")
    parser.add_argument(
        "--build-db",
        default="if-absent",
        choices=["never", "if-absent", "drop-then-build"],
        help="""
        Determines if the database is created:\n
            - never: *never* creates the database, not even if there does not exist one yet.
                Use this only if you expect the database to be created through other means, such
                as MySQL group replication.\n
            - if-absent: Creates a database only if none exists.\n
            - drop-then-build: Drops the database on startup to recreate it from scratch.
                THIS REMOVES ALL DATA PERMANENTLY. NO RECOVERY POSSIBLE.
        """,
    )
    parser.add_argument(
        "--reload",
        action=argparse.BooleanOptionalAction,
        help="Use `--reload` for FastAPI.",
    )
    return parser.parse_args()


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

    @app.get(url_prefix + "/authorization_test")
    def test_authorization(user: KeycloakUser = Depends(get_user_or_raise)) -> KeycloakUser:
        """
        Returns the user, if authenticated correctly.
        """
        return user

    @app.get(url_prefix + "/counts/v1")
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
        + uploader_routers.router_list
        + [review_router, user_router]
    ):
        app.include_router(router.create(url_prefix))


def create_app() -> FastAPI:
    """Create the FastAPI application, complete with routes."""
    setup_logger()
    args = _parse_args()
    assert_required_settings_configured()
    if args.build_db == "never":
        if not database_exists():
            logging.warning(
                "AI-on-Demand database does not exist on the MySQL server, "
                "but `build_db` is set to 'never'. If you are not creating the "
                "database through other means, such as MySQL group replication, "
                "this likely means that you will get errors or undefined behavior."
            )
    else:
        build_database(args)

    pyproject_toml = pkg_resources.get_distribution("aiod_metadata_catalogue")
    app = build_app(args.url_prefix, pyproject_toml.version)
    return app


def build_app(url_prefix: str = "", version: str = "dev"):
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
    return app


def build_database(args):
    drop_database = args.build_db == "drop-then-build"
    create_database(delete_first=drop_database)
    SQLModel.metadata.create_all(EngineSingleton().engine, checkfirst=True)
    with DbSession() as session:
        triggers = create_delete_triggers(AIoDConcept)
        for trigger in triggers:
            session.execute(trigger)
        existing_platforms = session.scalars(select(Platform)).all()
        missing_platforms = set(PlatformName) - {p.name for p in existing_platforms}
        if any(missing_platforms):
            session.add_all([Platform(name=name) for name in missing_platforms])
            session.commit()


def main():
    """Run the application. Placed in a separate function, to avoid having global variables"""
    args = _parse_args()
    uvicorn.run(
        "main:create_app",
        host="0.0.0.0",  # noqa: S104  # required to make the interface available outside of docker
        reload=args.reload,
        factory=True,
    )


if __name__ == "__main__":
    main()
