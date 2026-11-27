from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import connect
from app.db_init import init_db
from app.errors import register_exception_handlers
from app.routers import appointments, clinics, patients


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the tables once at start-up, using the same connection settings
    # (including the timezone) as every request.
    with connect() as conn:
        init_db(conn)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ClinicFlow API (M1)",
        version="0.1.0",
        lifespan=lifespan,
    )

    register_exception_handlers(app)

    @app.get("/health", tags=["Health"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(clinics.router, prefix="/v1")
    app.include_router(patients.router, prefix="/v1")
    app.include_router(appointments.router, prefix="/v1")

    return app


app = create_app()