"""
Punto de entrada del contenedor de procesamiento (consumidor de RabbitMQ).
"""
import time

from prometheus_client import start_http_server

from src.config.logging import get_logger
from src.database.indexes import create_indexes
from src.messaging.broker import start_consuming
from src.services.processing_service import process_earthquake_message

logger = get_logger("entrypoints.consumer")

PROMETHEUS_PORT = 9102


def main() -> None:
    start_http_server(PROMETHEUS_PORT)
    create_indexes()
    logger.info(f"Servicio de procesamiento iniciado. Metricas Prometheus en :{PROMETHEUS_PORT}/metrics")

    while True:
        try:
            start_consuming(process_earthquake_message)
        except Exception as error:
            # Si se pierde la conexion con RabbitMQ (por ejemplo se reinicio
            # el contenedor), esperamos un poco y lo intentamos de nuevo.
            logger.error(f"Se perdio la conexion con RabbitMQ: {error}. Reintentando en 5s...")
            time.sleep(5)


if __name__ == "__main__":
    main()
