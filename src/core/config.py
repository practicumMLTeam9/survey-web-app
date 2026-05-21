from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Значения по умолчанию — для локальной разработки
    PUBLIC_API_URL: str = "http://localhost:8000"  # Для внутренних ссылок API
    FRONTEND_URL: str = "http://localhost:5173"  # Для пользовательских ссылок

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # разрешить игнорировать поля из .env, которых нет в классе
    )


settings = Settings()