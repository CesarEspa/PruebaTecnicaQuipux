"""
Servicio de reportes.

Contiene las funciones que usa el DAG de Airflow. Las separamos del
archivo del DAG a proposito: asi se pueden probar con pruebas normales
de Python (sin necesitar Airflow corriendo) y el DAG queda como un
simple "orquestador" que llama a estas funciones en orden.
"""
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.config.constants import COLLECTION_EARTHQUAKES, COLLECTION_HOURLY_REPORTS
from src.config.logging import get_logger
from src.database.mongodb import get_db

logger = get_logger("services.reporting")

# Carpeta donde guardamos los archivos Parquet (bonus Nivel 4: "procesamiento
# de archivos Parquet en tiempo real o near real-time"). En Docker esta
# carpeta esta montada como volumen para que los archivos no se pierdan.
# Se puede sobreescribir con la variable de entorno DATA_LAKE_PATH (la usa
# el contenedor de Airflow, que corre con un directorio de trabajo distinto).
DATA_LAKE_PATH = Path(os.getenv("DATA_LAKE_PATH", "data/lake"))


def read_events_for_window(start: datetime, end: datetime) -> list[dict]:
    """Trae de Mongo todos los sismos guardados entre start (incluido) y end (excluido)."""
    db = get_db()
    cursor = db[COLLECTION_EARTHQUAKES].find(
        {"event_time": {"$gte": start, "$lt": end}}
    )
    return list(cursor)


def build_report(events: list[dict], report_date: datetime) -> dict:
    """Calcula el reporte consolidado a partir de una lista de sismos."""
    if not events:
        return {
            "report_date": report_date,
            "total_events": 0,
            "average_magnitude": 0.0,
            "max_magnitude": 0.0,
            "top_locations": [],
        }

    magnitudes = [event["magnitude"] for event in events]
    locations = [event["location"] for event in events]

    # Counter.most_common nos da las ubicaciones que mas se repiten, de
    # mayor a menor, sin tener que escribir el conteo a mano.
    top_locations = [place for place, _ in Counter(locations).most_common(3)]

    return {
        "report_date": report_date,
        "total_events": len(events),
        "average_magnitude": round(sum(magnitudes) / len(magnitudes), 3),
        "max_magnitude": max(magnitudes),
        "top_locations": top_locations,
    }


def save_report(report: dict) -> None:
    """Guarda (o actualiza) el reporte de esa hora en la coleccion hourly_reports."""
    db = get_db()
    db[COLLECTION_HOURLY_REPORTS].update_one(
        {"report_date": report["report_date"]}, {"$set": report}, upsert=True
    )
    logger.info(f"Reporte guardado para {report['report_date']}")


def export_events_to_parquet(events: list[dict], report_date: datetime) -> None:
    """
    Prueba de concepto del Nivel 4 (arquitectura de datos analitica):
    ademas de guardar en Mongo, dejamos una copia de los eventos crudos
    de esa hora en un archivo Parquet, particionado por fecha y hora.

    Parquet es un formato columnar pensado para analitica/Machine
    Learning (mucho mas eficiente para leer con pandas/Spark/DuckDB que
    leer todo desde Mongo). En una arquitectura real esto viviria en un
    almacenamiento tipo S3/MinIO; aqui usamos disco local para que el
    ejemplo funcione sin infraestructura extra.
    """
    if not events:
        logger.info("No hay eventos para exportar a Parquet en esta ventana")
        return

    for event in events:
        if "_id" in event:
            event["_id"] = str(event["_id"])  # ObjectId no es serializable a Parquet

    folder = DATA_LAKE_PATH / "bronze" / f"date={report_date.strftime('%Y-%m-%d')}"
    folder.mkdir(parents=True, exist_ok=True)

    file_path = folder / f"hour={report_date.strftime('%H')}.parquet"
    pd.DataFrame(events).to_parquet(file_path, index=False)

    logger.info(f"Eventos exportados a Parquet en {file_path}")
