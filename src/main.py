"""
Defines Rest API endpoints.

Note: order matters for overloaded paths
(https://fastapi.tiangolo.com/tutorial/path-params/#order-matters).
"""
import argparse

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.responses import HTMLResponse
from pydantic import Json
from sqlalchemy.engine import Engine
from sqlmodel import Session, select

import routers
from authentication import get_current_user
from config import KEYCLOAK_CONFIG
from database.deletion.triggers import add_delete_triggers
from database.model.concept.concept import AIoDConcept
from database.model.platform.platform import Platform
from database.model.platform.platform_names import PlatformName
from database.setup import sqlmodel_engine
from routers import resource_routers, parent_routers, enum_routers, search_routers


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


def add_routes(app: FastAPI, engine: Engine, url_prefix=""):
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
    def test_authorization(user: Json = Depends(get_current_user)) -> dict:
        """
        Returns the user, if authenticated correctly.
        """
        return {"msg": "success", "user": user}

    @app.get(url_prefix + "/counts/v1")
    def counts() -> dict:
        return {
            router.resource_name_plural: count
            for router in resource_routers.router_list
            if issubclass(router.resource_class, AIoDConcept)
            and (count := router.get_resource_count_func(engine)(detailed=True))
        }

    for router in (
        resource_routers.router_list
        + routers.other_routers
        + parent_routers.router_list
        + enum_routers.router_list
        + search_routers.router_list
    ):
        app.include_router(router.create(engine, url_prefix))


def create_app() -> FastAPI:
    """Create the FastAPI application, complete with routes."""
    args = _parse_args()
    app = FastAPI(
        openapi_url=f"{args.url_prefix}/openapi.json",
        docs_url=f"{args.url_prefix}/docs",
        swagger_ui_oauth2_redirect_url=f"{args.url_prefix}/docs/oauth2-redirect",
        swagger_ui_init_oauth={
            "clientId": KEYCLOAK_CONFIG.get("client_id_swagger"),
            "realm": KEYCLOAK_CONFIG.get("realm"),
            "appName": "AIoD Metadata Catalogue",
            "usePkceWithAuthorizationCodeGrant": True,
            "scopes": KEYCLOAK_CONFIG.get("scopes"),
        },
    )
    engine = sqlmodel_engine(args.rebuild_db)
    with engine.connect() as connection:
        AIoDConcept.metadata.create_all(connection, checkfirst=True)
        connection.commit()
    with Session(engine) as session:
        existing_platforms = session.scalars(select(Platform)).all()
        if not any(existing_platforms):
            session.add_all([Platform(name=name) for name in PlatformName])
            session.commit()

            # this is a bit of a hack: instead of checking whether the triggers exist, we check
            # whether platforms are already present. If platforms were not present, the db is
            # empty, and so the triggers should still be added.
            add_delete_triggers(AIoDConcept)

    add_routes(app, engine, url_prefix=args.url_prefix)
    return app


def main():
    """Run the application. Placed in a separate function, to avoid having global variables"""
    args = _parse_args()
    uvicorn.run("main:create_app", host="0.0.0.0", reload=args.reload, factory=True)


if __name__ == "__main__":
    main()
