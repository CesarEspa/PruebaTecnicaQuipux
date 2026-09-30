"""
Configuracion de logging "estructurado" (bonus Nivel 1).

En vez de imprimir texto libre, cada linea de log se imprime como un
objeto JSON. Esto es util porque herramientas como Grafana/Loki o el
"docker logs" pueden parsear cada linea facilmente.

No usamos ninguna libreria externa para esto, solo un Formatter
personalizado de la libreria estandar "logging". Tampoco dependemos de
src.config.settings aqui, para que este modulo tambien lo pueda usar el
DAG de Airflow sin instalar pydantic-settings en esa imagen.
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": record.name,
            "message": record.getMessage(),
        }
        # Si el log fue llamado con exc_info=True, agregamos el traceback.
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """Crea (o reutiliza) un logger configurado con salida JSON a stdout."""
    logger = logging.getLogger(name)

    # Evita agregar handlers duplicados si la funcion se llama varias veces.
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    logger.addHandler(handler)
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))
    return logger
