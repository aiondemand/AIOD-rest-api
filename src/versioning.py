from datetime import datetime, timezone

from fastapi import FastAPI
from starlette.requests import Request


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


def add_deprecation_and_sunset_header_data(app: FastAPI):
    app.middleware("http")(add_deprecation_header)
    app.middleware("http")(add_sunset_header)
    # Adds a visual deprecation style to the generated docs:
    for route in app.routes:
        if "v1" in route.path:
            route.deprecated = True
