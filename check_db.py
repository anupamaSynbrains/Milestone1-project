# file for checking the database connection and retrieving clinic codes
import psycopg
from app.config import get_settings
from app.db_init import init_db
# file for checking the database connection and retrieving clinic codes
settings = get_settings()
# connect to the database and retrieve clinic codes
with psycopg.connect(settings.database_url) as conn:
    init_db(conn)
    # retrieve clinic codes from the database
    clinics = conn.execute("SELECT code FROM clinics ORDER BY code").fetchall()
    print("Clinics:", clinics)