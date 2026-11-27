from collections.abc import Generator
import psycopg
from app.config import settings


def connect(app_timezone: str | None = None) -> psycopg.Connection:
    tz = app_timezone or settings.app_timezone
    return psycopg.connect(
        settings.database_url,
        options=f"-c timezone={tz}",
    )


def get_db() -> Generator[psycopg.Connection, None, None]:
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
