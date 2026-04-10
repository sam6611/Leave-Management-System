from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Automated Leave Approval System"
    database_url: str = "postgresql+asyncpg://postgres:Sam@3201@localhost:5432/slms"
    jwt_secret: str = "change-this-secret"
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 60

# fj

settings = Settings()
