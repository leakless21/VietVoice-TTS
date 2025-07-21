from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    """Defines the application's configuration."""
    # Define your configuration variables here
    TMP_DIR_PATH: Path = Path("/tmp/vietvoice_api_cache")
    FILE_LIFESPAN_SECONDS: int = 3600  # Default lifespan for cached files in seconds
    
    # This tells pydantic to load variables from a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# Create a single, reusable settings instance
settings = Settings()