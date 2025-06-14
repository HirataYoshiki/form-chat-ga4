from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # AI Agent Settings
    # The default value will be used if the environment variable is not set.
    gemini_model_name: str = "gemini-1.5-flash-latest"

    # API key is optional at this level.
    # Code using this setting should handle the case where it might be None.
    google_api_key: Optional[str] = None

    # Supabase Connection Settings
    supabase_url: Optional[str] = None
    supabase_service_role_key: Optional[str] = None

    # Supabase Auth Settings
    supabase_jwks_uri: Optional[str] = None
    supabase_jwt_audience: str = "authenticated" # Default value
    # supabase_jwt_issuer: Optional[str] = None # Optional: if not set, can be derived from supabase_url

    # AI Agent Retry Settings
    ai_agent_retry_attempts: int = 3
    ai_agent_retry_wait_initial_seconds: int = 1
    ai_agent_retry_wait_max_seconds: int = 10
    ai_agent_retry_wait_multiplier: int = 2

    # Vertex AI RAG Settings
    PROJECT_ID: Optional[str] = None
    VERTEX_AI_REGION: str = "us-central1"
    RAG_GCS_BUCKET_UPLOADS: Optional[str] = None
    RAG_GCS_BUCKET_PROCESSED: Optional[str] = None
    DEFAULT_RAG_CHUNK_SIZE: int = 1000
    DEFAULT_RAG_CHUNK_OVERLAP: int = 200
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None

    # Configuration for loading from .env file
    # This uses Pydantic V2 (pydantic-settings) style.
    # For Pydantic V1, you would use:
    # class Config:
    #     env_file = ".env"
    #     env_file_encoding = 'utf-8'
    #     extra = 'ignore' # Allow extra fields in the .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore' # 'extra' allows other environment variables to exist without causing validation errors
    )

# Create a single, importable instance of the settings.
# Other parts of the application will import this instance.
settings = Settings()

# Example of how to use this in other modules:
#
# from backend.config import settings
#
# def some_function():
#     model = settings.gemini_model_name
#     api_key = settings.google_api_key
#     if api_key:
#         print(f"Using API Key: {api_key[:5]}...") # Be careful with logging API keys
#     else:
#         print("Google API Key is not set.")
#     print(f"Using Gemini Model: {model}")
