from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from database.session import DbSession
from database.model.access.access_log import AssetAccessLog
from middleware.path_parse import parse_asset_from_path


class AccessLogMiddleware(BaseHTTPMiddleware):
    """Write one AssetAccessLog row for any asset route."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        parsed = parse_asset_from_path(request.url.path)
        if parsed:
            resource_type, asset_id = parsed
            entry = AssetAccessLog(
                asset_id=asset_id,
                resource_type=resource_type,
                status=response.status_code,
            )
            with DbSession() as sess:
                sess.add(entry)
                sess.commit()

        return response
