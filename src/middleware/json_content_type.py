from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class JsonContentTypeMiddleware(BaseHTTPMiddleware):
    """Enforce JSON Content-Type for write requests with request bodies."""

    _METHODS_TO_VALIDATE = {"POST", "PUT", "PATCH"}

    @staticmethod
    def _is_docs_path(path: str) -> bool:
        return any(
            path.startswith(p) or path.endswith(p)
            for p in ("/docs", "/redoc", "/openapi.json")
        )

    @staticmethod
    def _is_multipart_image_upload(path: str) -> bool:
        segments = [segment for segment in path.strip("/").split("/") if segment]
        return len(segments) >= 3 and segments[-3] == "organisations" and segments[-1] == "image"

    @staticmethod
    def _has_request_body(request: Request) -> bool:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                return int(content_length) > 0
            except ValueError:
                return True
        return "transfer-encoding" in request.headers

    async def dispatch(self, request: Request, call_next):
        if request.method not in self._METHODS_TO_VALIDATE:
            return await call_next(request)

        path = request.url.path
        if self._is_docs_path(path) or self._is_multipart_image_upload(path):
            return await call_next(request)

        if not self._has_request_body(request):
            return await call_next(request)

        content_type = request.headers.get("content-type", "")
        if not content_type.lower().startswith("application/json"):
            return JSONResponse(
                status_code=415,
                content={"detail": "Content-Type must include 'application/json'."},
            )

        response: Response = await call_next(request)
        return response
