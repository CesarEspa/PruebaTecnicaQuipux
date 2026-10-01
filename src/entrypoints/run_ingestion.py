"""Arranca el contenedor de ingesta: cada N segundos llama al servicio de ingesta."""
import time

from prometheus_client import start_http_server

from src.config.logging import get_logger
from src.config.settings import settings
from src.services.ingestion_service import run_ingestion_cycle

logger = get_logger("entrypoints.ingestion")

PROMETHEUS_PORT = 9101
RETRY_SECONDS = 10


def main() -> None:
    start_http_server(PROMETHEUS_PORT)
    logger.info(f"Servicio de ingesta iniciado. Metricas Prometheus en :{PROMETHEUS_PORT}/metrics")
    logger.info(f"Consultando la API de USGS cada {settings.ingestion_interval_seconds} segundos")

    while True:
        try:
            run_ingestion_cycle()
            time.sleep(settings.ingestion_interval_seconds)
        except Exception as error:
            # Si RabbitMQ todavia no estaba listo (pasa justo al arrancar todo
            # junto con docker compose), reintenta pronto en vez de esperar
            # el intervalo completo.
            logger.error(f"Error inesperado en el ciclo de ingesta: {error}")
            time.sleep(RETRY_SECONDS)


if __name__ == "__main__":
    main()
