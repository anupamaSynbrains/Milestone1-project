# database connection module for FastAPI application
from collections.abc import Generator
from fastapi import Request
#psycopg is a PostgreSQL database adapter for Python that provides a way to connect to and interact with PostgreSQL databases. It is designed to be efficient, easy to use, and compatible with the latest PostgreSQL features.
import psycopg

# Function to get a database connection from the FastAPI request object. It retrieves the database URL from the application state and establishes a connection using psycopg. The function yields the connection, allowing it to be used within a context manager, and ensures that the connection is properly closed after use.
def get_conn(request: Request) -> Generator[psycopg.Connection, None, None]:
    db_url: str = request.app.state.database_url
    with psycopg.connect(db_url) as conn:
        yield conn