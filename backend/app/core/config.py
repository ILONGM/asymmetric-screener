from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    anthropic_api_key: str
    google_client_id: str
    google_client_secret: str
    secret_key: str

    class Config:
        env_file = ".env"


settings = Settings()
