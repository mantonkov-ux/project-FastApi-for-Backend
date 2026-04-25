# config.py

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    LOG_PRINT: str = "1"
    DATABASE_URL: str
    AUTH_SECRET_KEY: str
    AUTH_TOKEN_EXPIRE_MINUTES: int
    LLM_BASE_URL: str
    LLM_MODEL: str
    LLM_API_KEY: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"   
    )

settings = Settings()