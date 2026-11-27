from contextlib import asynccontextmanager
from fastapi import FastAPI
import psycopg
from app.config import get_settings
from app.db_init import init_db
from app.errors import register_exception_handlers
from app.routers import appointments, clinics, patients


app.state.app_timezone = settings.app_timezone

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.database_url = settings.database_url
    with psycopg.connect(settings.database_url) as conn:
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

    app.include_router(clinics.router)
    app.include_router(patients.router)
    app.include_router(appointments.router)

    return app


app = create_app()