"""
Centralized error handling.

Domain code should raise the exceptions defined here rather than raw
HTTPException, so error responses stay consistent and easy to test.
"""
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


class ContextIQError(Exception):
    """Base class for all domain-level errors."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    default_message: str = "Something went wrong."

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class NotFoundError(ContextIQError):
    status_code = status.HTTP_404_NOT_FOUND
    default_message = "Resource not found."


class ForbiddenError(ContextIQError):
    status_code = status.HTTP_403_FORBIDDEN
    default_message = "You do not have access to this resource."


class ConflictError(ContextIQError):
    status_code = status.HTTP_409_CONFLICT
    default_message = "Resource conflict."


def _error_body(message: str, error_type: str) -> dict:
    return {"error": {"type": error_type, "message": message}}


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to the FastAPI app instance."""

    @app.exception_handler(ContextIQError)
    async def handle_contextiq_error(request: Request, exc: ContextIQError):
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.message, exc.__class__.__name__),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body("Validation failed.", "ValidationError")
            | {"details": exc.errors()},
        )

    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(request: Request, exc: IntegrityError):
        logger.warning("Database integrity error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=_error_body(
                "Database integrity constraint violated (e.g. duplicate or invalid reference).",
                "IntegrityError",
            ),
        )

    @app.exception_handler(SQLAlchemyError)
    async def handle_sqlalchemy_error(request: Request, exc: SQLAlchemyError):
        logger.exception("Database failure on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body("Database error.", "DatabaseError"),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        logger.exception("Unhandled request failure on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body("Internal server error.", "InternalError"),
        )
