import json
import logging
import traceback
import uuid
from http import HTTPStatus

from fastapi import HTTPException, status
from pydantic import BaseModel
from starlette.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


def as_http_exception(exception: Exception) -> HTTPException:
    if isinstance(exception, HTTPException):
        return exception
    traceback.print_exc()
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=(
            "Unexpected exception while processing your request. Please contact the maintainers: "
            f"{exception}"
        ),
    )


class ErrorSchema(BaseModel):
    detail: str
    reference: str


async def _get_body_content(request) -> str:
    body = getattr(request, "_body", None)
    if body is None:
        try:
            body = await request.body()
        except RuntimeError:
            # The request body stream may already be consumed by the request handler.
            # In that case FastAPI/Starlette raises RuntimeError when attempting to read it again.
            return "<Data Stream with unknown content>"

    if not body:
        return ""

    try:
        return json.dumps(json.loads(body))
    except (json.JSONDecodeError, TypeError):
        if isinstance(body, bytes):
            return body.decode("utf-8", errors="replace")
        return str(body)


async def http_exception_handler(request, exc):
    reference = uuid.uuid4().hex
    error = ErrorSchema(detail=exc.detail, reference=reference)
    content = error.dict()

    body_content = await _get_body_content(request)

    log_message = json.dumps(
        {
            "reference": reference,
            "exception": f"{str(exc)!r}",
            "method": request.scope["method"],
            "path": request.scope["path"],
            "body": body_content,
        }
    )
    log_level = logging.DEBUG
    if exc.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
        log_level = logging.WARNING
    logging.log(log_level, log_message)
    return JSONResponse(content, status_code=exc.status_code)


async def validation_exception_handler(request, exc: RequestValidationError):
    reference = uuid.uuid4().hex

    body_content = await _get_body_content(request)

    log_message = {
        "reference": reference,
        "exception": str(exc),
        "method": request.scope["method"],
        "path": request.scope["path"],
        "body": body_content,
    }

    logging.debug(str(log_message))

    content = {
        "detail": exc.errors(),
        "reference": reference,
    }

    return JSONResponse(content, status_code=422)
