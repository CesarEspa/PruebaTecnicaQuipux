"""Modelo del documento de metricas en tiempo real (coleccion 'metrics')."""
from pydantic import BaseModel, Field


class HourlyMetric(BaseModel):
    """Un documento por cada hora (window="2026-06-17T10"), se va actualizando con cada sismo nuevo."""

    window: str
    earthquake_count: int = 0
    avg_magnitude: float = 0.0
    max_magnitude: float = 0.0
    sum_magnitude: float = 0.0  # para poder recalcular el promedio sin releer todo
    magnitude_distribution: dict[str, int] = Field(default_factory=dict)
