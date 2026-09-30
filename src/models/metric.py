"""Modelo del documento de metricas en tiempo real (coleccion 'metrics')."""
from pydantic import BaseModel, Field


class HourlyMetric(BaseModel):
    """
    Un documento por cada ventana de una hora, por ejemplo window="2026-06-17T10".
    Se va actualizando cada vez que llega un sismo nuevo en esa hora.

    magnitude_distribution es un diccionario {nombre_del_rango: cantidad},
    por ejemplo {"light": 5, "moderate": 2}. Usar un diccionario en vez de
    una lista hace que actualizar el contador de un rango sea un simple
    "$inc" de Mongo, sin tener que buscar dentro de un arreglo.
    """

    window: str
    earthquake_count: int = 0
    avg_magnitude: float = 0.0
    max_magnitude: float = 0.0
    # Suma de todas las magnitudes de la ventana, se usa para recalcular el
    # promedio sin tener que leer todos los eventos otra vez.
    sum_magnitude: float = 0.0
    magnitude_distribution: dict[str, int] = Field(default_factory=dict)
