"""
Punto de entrada del contenedor de ingesta.

Es un script muy simple: cada N segundos llama al servicio de ingesta.
No usamos ninguna libreria de "scheduling" para mantenerlo facil de leer.
"""
import time

from prometheus_client import start_http_server

from src.config.logging import get_logger
from src.config.settings import settings
from src.services.ingestion_service import run_ingestion_cycle

logger = get_logger("entrypoints.ingestion")

PROMETHEUS_PORT = 9101


def main() -> None:
    start_http_server(PROMETHEUS_PORT)
    logger.info(f"Servicio de ingesta iniciado. Metricas Prometheus en :{PROMETHEUS_PORT}/metrics")
    logger.info(f"Consultando la API de USGS cada {settings.ingestion_interval_seconds} segundos")

    while True:
        try:
            run_ingestion_cycle()
        except Exception as error:
            # Cualquier error inesperado se registra pero NO tumba el servicio:
            # simplemente intentamos de nuevo en el siguiente ciclo.
            logger.error(f"Error inesperado en el ciclo de ingesta: {error}")

        time.sleep(settings.ingestion_interval_seconds)


if __name__ == "__main__":
    main()
