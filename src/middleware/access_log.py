from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlmodel import Session

from database.session import DbSession
from database.model.access.access_log import AssetAccessLog
from authentication import get_user_or_none

from middleware.resource_types import all_resource_types
VALID_TYPES = all_resource_types()   # calculated once at import time


async def _get_optional_user(request: Request):
    """Return Keycloak user or None (don’t raise if unauthenticated)."""
    try:
        return await get_user_or_none(request)
    except Exception:  # unauthenticated / no token
        return None


class AccessLogMiddleware(BaseHTTPMiddleware):
    """Write one AssetAccessLog row for /datasets/<id> and /models/<id>."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        segments = request.url.path.strip("/").split("/")
        if len(segments) >= 2 and segments[0] in VALID_TYPES:
            resource_type = segments[0]                
            asset_id     = "/".join(segments[1:])       
            user = await _get_optional_user(request)

            entry = AssetAccessLog(
                asset_id=asset_id,
                resource_type=resource_type,
                status=response.status_code,
            )
            with DbSession() as sess:
                sess.add(entry)
                sess.commit()

        return response
