"""Configuracion de la app, leida desde variables de entorno."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Las variables de Mongo no van aqui: se leen con os.getenv directo en
    # database/mongodb.py y config/logging.py para que Airflow tambien
    # pueda usar esos dos modulos sin instalar pydantic-settings.

    rabbitmq_user: str = "admin"
    rabbitmq_password: str = "admin123"
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672

    usgs_api_url: str = (
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
    )
    ingestion_interval_seconds: int = 180

    cache_ttl_seconds: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
