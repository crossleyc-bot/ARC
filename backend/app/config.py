from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://arc:arc_password@localhost:5432/arc_db"

    # Power BI
    POWERBI_CLIENT_ID: str = ""
    POWERBI_CLIENT_SECRET: str = ""
    POWERBI_TENANT_ID: str = ""

    # Cognos
    COGNOS_BASE_URL: str = ""
    COGNOS_NAMESPACE: str = ""
    COGNOS_USERNAME: str = ""
    COGNOS_PASSWORD: str = ""

    # AI
    ANTHROPIC_API_KEY: str = ""

    # App
    SECRET_KEY: str = "change-me-in-production"
    CORS_ORIGINS: str = "http://localhost:5173"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
