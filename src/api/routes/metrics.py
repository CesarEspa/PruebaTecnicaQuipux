from datetime import datetime, timezone

from fastapi import APIRouter, Query, Request
from pymongo import DESCENDING

from src.config.constants import COLLECTION_METRICS
from src.database.mongodb import get_db
from src.utils.serializers import serialize_doc
from src.utils.time_windows import get_hour_window

router = APIRouter()


@router.get("/metrics")
def list_metrics(
    request: Request,
    window: str | None = Query(default=None, description="Ej: 2026-06-17T10"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
):
    """
    Devuelve las metricas por hora (cantidad de sismos, magnitud promedio,
    magnitud maxima y distribucion por rango).

    Se puede pedir una ventana especifica con ?window=2026-06-17T10, o si
    no se manda nada, se listan todas ordenadas de la mas reciente a la
    mas antigua.
    """
    cache = request.app.state.cache
    cache_key = f"metrics:{window}:{page}:{page_size}"

    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    db = get_db()

    if window:
        doc = db[COLLECTION_METRICS].find_one({"window": window})
        result = serialize_doc(doc) if doc else {"error": "No hay metricas para esa ventana"}
        cache.set(cache_key, result)
        return result

    skip = (page - 1) * page_size
    cursor = (
        db[COLLECTION_METRICS]
        .find({})
        .sort("window", DESCENDING)
        .skip(skip)
        .limit(page_size)
    )
    total = db[COLLECTION_METRICS].count_documents({})

    result = {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [serialize_doc(doc) for doc in cursor],
    }
    cache.set(cache_key, result)
    return result


@router.get("/metrics/current")
def get_current_metrics(request: Request):
    """Atajo para consultar la metrica de la hora actual sin tener que calcular el texto de la ventana."""
    window = get_hour_window(datetime.now(timezone.utc))
    return list_metrics(request=request, window=window, page=1, page_size=1)
