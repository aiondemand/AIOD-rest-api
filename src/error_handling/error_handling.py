import json
import logging
import traceback
import uuid
from http import HTTPStatus

from fastapi import HTTPException, status
from pydantic import BaseModel
from starlette.responses import JSONResponse


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


async def http_exception_handler(request, exc):
    reference = uuid.uuid4().hex
    error = ErrorSchema(detail=exc.detail, reference=reference)
    content = error.dict()

    body_content = "<Data Stream with unknown content>"
    if not request._stream_consumed:
        body = await request.body()
        body_content = json.dumps(json.loads(body)) if body else ""

    log_message = str(
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
