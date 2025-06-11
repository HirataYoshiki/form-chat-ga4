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

    # AI Agent Retry Settings
    ai_agent_retry_attempts: int = 3
    ai_agent_retry_wait_initial_seconds: int = 1
    ai_agent_retry_wait_max_seconds: int = 10
    ai_agent_retry_wait_multiplier: int = 2

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
