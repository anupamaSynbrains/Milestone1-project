# Configuration settings for the application.
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

# dataclass to hold the application settings and help with type checking and immutability.
#frozen=True makes the dataclass immutable, meaning that once an instance is created, its attributes cannot be modified. This is useful for configuration settings that should not change during the application's runtime.
@dataclass(frozen=True)
class Settings:
    database_url: str
    test_database_url: str
    log_level: str

# Function to retrieve settings from environment variables or .env file.the function raises a RuntimeError if the DATABASE_URL is not set. also, it provides a default value for the log_level if not specified.
def get_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL", "")
    test_database_url = os.getenv("TEST_DATABASE_URL", "")
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    # Check if the database_url is not set, and raise a RuntimeError if it is missing. This ensures that the application has the necessary configuration to connect to the database.
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set in environment or .env")
    return Settings(
        # Initialize the settings with the retrieved values
        database_url=database_url,
        test_database_url=test_database_url or database_url,
        log_level=log_level,
    )