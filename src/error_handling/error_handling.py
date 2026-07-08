import json
import logging
import traceback
from http import HTTPStatus

from fastapi import HTTPException, status
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

async def http_exception_handler(request, exc):
    # 1.access the 'Single Source of Truth' id from your middleware this is the 'correlation_id' we set in the CorrelationIdMiddleware
    correlation_id = getattr(request.state, "correlation_id", "unknown")

    # 2.hey team built the rfc7807 'Problem Details' structure this should help
    
    content = {
        "type": "about:blank",
        "title": HTTPStatus(exc.status_code).phrase,
        "status": exc.status_code,
        "detail": exc.detail,
        "instance": request.url.path,
        "correlation_id": correlation_id 
    }

    # 3.enhanced logging logic log the error with all relevant details, including the correlation id, request method, path, and exception details. This will help in debugging and tracing issues effectively.
    body_content = "<Data Stream with unknown content>"
    if not request._stream_consumed:
        try:
            body = await request.body()
            body_content = json.loads(body) if body else ""
        except Exception:
            body_content = "<Unparseable Body>"

        try:
            body = await request.body()
            body_content = json.loads(body) if body else ""
        except Exception:
            body_content = ""

        try:
            safe_reference = reference
        except NameError:
            safe_reference = getattr(getattr(request, "state", None), "reference", "UNKNOWN")

        log_data = {
            "correlation_id": correlation_id,
            "reference": safe_reference,
            "status_code": exc.status_code,
            "method": request.scope.get("method", getattr(request, "method", "UNKNOWN")),
            "path": request.scope.get("path", getattr(getattr(request, "url", None), "path", "UNKNOWN")),
            "exception": f"{str(exc)!r}",
            "body": body_content,
        }

        log_level = logging.WARNING if exc.status_code >= 500 else logging.INFO
        logging.log(log_level, f"API Error: {json.dumps(log_data)}")


        return JSONResponse(
            content=content,
            status_code=exc.status_code,
            media_type="application/problem+json"
        )