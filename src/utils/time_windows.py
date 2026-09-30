"""Funciones pequenas para trabajar con ventanas de tiempo por hora."""
from datetime import datetime


def get_hour_window(moment: datetime) -> str:
    """Convierte una fecha a texto tipo '2026-06-17T10' (la hora exacta, sin minutos)."""
    return moment.strftime("%Y-%m-%dT%H")
