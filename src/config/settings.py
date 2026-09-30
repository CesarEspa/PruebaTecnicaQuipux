"""
Configuracion central de la aplicacion.

Usamos pydantic-settings para leer las variables de entorno una sola vez
y tener autocompletado + validacion de tipos en vez de usar os.environ
regado por todo el codigo.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Nota: las variables de Mongo (MONGO_USER, MONGO_HOST, etc.) no estan
    # aqui a proposito. Se leen directamente con os.getenv en
    # src/database/mongodb.py y src/config/logging.py, para que esos dos
    # modulos los pueda usar tambien el DAG de Airflow sin necesitar
    # pydantic-settings instalado en esa imagen.

    # RabbitMQ
    rabbitmq_user: str = "admin"
    rabbitmq_password: str = "admin123"
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672

    # USGS API
    usgs_api_url: str = (
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
    )
    ingestion_interval_seconds: int = 180

    # Cache
    cache_ttl_seconds: int = 30

    # extra="ignore": el archivo .env tiene variables de otros modulos
    # (Mongo, Grafana, etc.) que esta clase no necesita conocer.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Una sola instancia compartida por toda la app (patron singleton simple).
settings = Settings()
