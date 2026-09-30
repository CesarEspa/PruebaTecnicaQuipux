"""
Schemas (con Pydantic) para validar los parametros que llegan a la API.
Separarlos aqui hace que las rutas de FastAPI queden mas limpias.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class EarthquakeFilterParams(BaseModel):
    """Filtros, paginacion y orden para GET /earthquakes."""

    min_magnitude: Optional[float] = Field(default=None, ge=0)
    max_magnitude: Optional[float] = Field(default=None, ge=0)
    location: Optional[str] = None

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)

    sort_by: Literal["event_time", "magnitude"] = "event_time"
    order: Literal["asc", "desc"] = "desc"


class ReportFilterParams(BaseModel):
    """Filtros y paginacion para GET /reports."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)
