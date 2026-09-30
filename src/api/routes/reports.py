from typing import Annotated

from fastapi import APIRouter, Query, Request
from pymongo import DESCENDING

from src.config.constants import COLLECTION_HOURLY_REPORTS
from src.database.mongodb import get_db
from src.metadata.schemas import ReportFilterParams
from src.utils.serializers import serialize_doc

router = APIRouter()


@router.get("/reports")
def list_reports(request: Request, filters: Annotated[ReportFilterParams, Query()]):
    """Lista los reportes horarios generados por el DAG de Airflow, del mas reciente al mas antiguo."""
    cache = request.app.state.cache
    cache_key = f"reports:{filters.page}:{filters.page_size}"

    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    db = get_db()
    skip = (filters.page - 1) * filters.page_size

    cursor = (
        db[COLLECTION_HOURLY_REPORTS]
        .find({})
        .sort("report_date", DESCENDING)
        .skip(skip)
        .limit(filters.page_size)
    )
    total = db[COLLECTION_HOURLY_REPORTS].count_documents({})

    result = {
        "total": total,
        "page": filters.page,
        "page_size": filters.page_size,
        "items": [serialize_doc(doc) for doc in cursor],
    }
    cache.set(cache_key, result)
    return result
