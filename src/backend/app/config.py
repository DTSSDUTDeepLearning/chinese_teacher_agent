from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    deepseek_api_key: str
    database_url: str = "mysql+aiomysql://user:password@localhost:3306/chinese_teacher"
    redis_url: str = "redis://localhost:6379/0"
    app_env: str = "development"


settings = Settings()
