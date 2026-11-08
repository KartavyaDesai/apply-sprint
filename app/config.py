from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "ApplySprint"
    environment: str = "development"
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_storage_bucket: str = "application-documents"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    max_upload_mb: int = 15
    request_timeout_seconds: int = 25
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
