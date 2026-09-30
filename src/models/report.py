"""Modelo del reporte horario que genera el DAG de Airflow."""
from datetime import datetime

from pydantic import BaseModel


class HourlyReport(BaseModel):
    report_date: datetime
    total_events: int
    average_magnitude: float
    max_magnitude: float
    top_locations: list[str]
