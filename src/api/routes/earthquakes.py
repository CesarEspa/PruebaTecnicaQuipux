from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pymongo import ASCENDING, DESCENDING

from src.config.constants import COLLECTION_EARTHQUAKES
from src.database.mongodb import get_db
from src.metadata.schemas import EarthquakeFilterParams
from src.utils.serializers import serialize_doc

router = APIRouter()


@router.get("/earthquakes")
def list_earthquakes(filters: Annotated[EarthquakeFilterParams, Query()]):
    """Lista los sismos guardados, con filtros, orden y paginacion."""
    db = get_db()

    query: dict = {}
    if filters.min_magnitude is not None or filters.max_magnitude is not None:
        query["magnitude"] = {}
        if filters.min_magnitude is not None:
            query["magnitude"]["$gte"] = filters.min_magnitude
        if filters.max_magnitude is not None:
            query["magnitude"]["$lte"] = filters.max_magnitude

    if filters.location:
        query["location"] = {"$regex": filters.location, "$options": "i"}  # "i" = sin distinguir mayus/minus

    sort_direction = ASCENDING if filters.order == "asc" else DESCENDING
    skip = (filters.page - 1) * filters.page_size

    cursor = (
        db[COLLECTION_EARTHQUAKES]
        .find(query)
        .sort(filters.sort_by, sort_direction)
        .skip(skip)
        .limit(filters.page_size)
    )

    total = db[COLLECTION_EARTHQUAKES].count_documents(query)

    return {
        "total": total,
        "page": filters.page,
        "page_size": filters.page_size,
        "items": [serialize_doc(doc) for doc in cursor],
    }


@router.get("/earthquakes/{event_id}")
def get_earthquake(event_id: str):
    """Devuelve el detalle de un sismo por su event_id (no por el _id de Mongo)."""
    db = get_db()
    doc = db[COLLECTION_EARTHQUAKES].find_one({"event_id": event_id})

    if doc is None:
        raise HTTPException(status_code=404, detail="Sismo no encontrado")

    return serialize_doc(doc)
