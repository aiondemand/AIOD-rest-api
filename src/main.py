"""
Defines Rest API endpoints.

Note: order matters for overloaded paths
(https://fastapi.tiangolo.com/tutorial/path-params/#order-matters).
"""
import argparse
import logging

import pkg_resources
import uvicorn
from fastapi import Depends, FastAPI
from fastapi.responses import HTMLResponse
from sqlmodel import select

from authentication import get_current_user, User
from config import KEYCLOAK_CONFIG
from database.deletion.triggers import add_delete_triggers
from database.model.concept.concept import AIoDConcept
from database.model.platform.platform import Platform
from database.model.platform.platform_names import PlatformName
from database.session import EngineSingleton, DbSession
from database.setup import drop_or_create_database, database_exists
from routers import resource_routers, parent_routers, enum_routers, uploader_routers
from routers import search_routers
from setup_logger import setup_logger


def _parse_args() -> argparse.Namespace:
    # TODO: refactor configuration (https://github.com/aiondemand/AIOD-rest-api/issues/82)
    parser = argparse.ArgumentParser(description="Please refer to the README.")
    parser.add_argument("--url-prefix", default="", help="Prefix for the api url.")
    parser.add_argument(
        "--rebuild-db",
        default="only-if-empty",
        choices=["no", "only-if-empty", "always"],
        help="Determines if the database is recreated.",
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
    def test_authorization(user: User = Depends(get_current_user)) -> User:
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
    ):
        app.include_router(router.create(url_prefix))


def create_app() -> FastAPI:
    """Create the FastAPI application, complete with routes."""
    setup_logger()
    args = _parse_args()
    pyproject_toml = pkg_resources.get_distribution("aiod_metadata_catalogue")
    app = FastAPI(
        openapi_url=f"{args.url_prefix}/openapi.json",
        docs_url=f"{args.url_prefix}/docs",
        title="AIoD Metadata Catalogue",
        description="This is the Swagger documentation of the AIoD Metadata Catalogue. For the "
        "Changelog, refer to "
        '<a href="https://github.com/aiondemand/AIOD-rest-api/releases">https'
        "://github.com/aiondemand/AIOD-rest-api/releases</a>.",
        version=pyproject_toml.version,
        swagger_ui_oauth2_redirect_url=f"{args.url_prefix}/docs/oauth2-redirect",
        swagger_ui_init_oauth={
            "clientId": KEYCLOAK_CONFIG.get("client_id_swagger"),
            "realm": KEYCLOAK_CONFIG.get("realm"),
            "appName": "AIoD Metadata Catalogue",
            "usePkceWithAuthorizationCodeGrant": True,
            "scopes": KEYCLOAK_CONFIG.get("scopes"),
        },
    )
    if args.rebuild_db == "no":
        if not database_exists():
            logging.warning(
                "AI-on-Demand database does not exist on the MySQL server, "
                "but `rebuild_db` is set to 'no'. If you are not creating the "
                "database through other means, such as MySQL group replication, "
                "this likely means that you will get errors or undefined behavior."
            )
    else:
        drop_or_create_database(delete_first=args.rebuild_db == "always")
        AIoDConcept.metadata.create_all(EngineSingleton().engine, checkfirst=True)
        with DbSession() as session:
            existing_platforms = session.scalars(select(Platform)).all()
            if not any(existing_platforms):
                session.add_all([Platform(name=name) for name in PlatformName])
                session.commit()

                # this is a bit of a hack: instead of checking whether the triggers exist, we check
                # whether platforms are already present. If platforms were not present, the db is
                # empty, and so the triggers should still be added.
                add_delete_triggers(AIoDConcept)

    add_routes(app, url_prefix=args.url_prefix)
    return app


def main():
    """Run the application. Placed in a separate function, to avoid having global variables"""
    args = _parse_args()
    uvicorn.run("main:create_app", host="0.0.0.0", reload=args.reload, factory=True)


if __name__ == "__main__":
    main()
