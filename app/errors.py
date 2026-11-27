from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import psycopg

class ClinicFlowError(Exception):
    """Base application error for ClinicFlow domain rules."""

    def __init__(self, message: str, status_code: int = 400, code: str = "BAD_REQUEST") -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code

class NotFoundError(ClinicFlowError):
    def __init__(self, message: str = "Resource not found", code: str = "NOT_FOUND") -> None:
        super().__init__(message=message, status_code=404, code=code)


class ConflictError(ClinicFlowError):
    def __init__(self, message: str = "Resource conflict", code: str = "CONFLICT") -> None:
        super().__init__(message=message, status_code=409, code=code)


class RuleViolationError(ClinicFlowError):
    def __init__(self, message: str, code: str = "RULE_VIOLATION", status_code: int = 422) -> None:
        super().__init__(message=message, status_code=status_code, code=code)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ClinicFlowError)
    async def handle_clinicflow_error(_request: Request, exc: ClinicFlowError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}},
    )
    

    @app.exception_handler(psycopg.Error)
    async def handle_psycopg_error(_request: Request, exc: psycopg.Error) -> JSONResponse:
        sqlstate = getattr(exc, "sqlstate", None)
        if sqlstate == "23P01":
            return JSONResponse(
                status_code=409,
                content={
                    "error": {
                        "code": "APPOINTMENT_CONFLICT",
                        "message": "Doctor already has an active appointment in this time slot.",
                    }
                },
            )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "DATABASE_ERROR",
                    "message": "A database error occurred while processing the request.",
                }
            },
        )