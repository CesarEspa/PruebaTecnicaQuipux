"""Aplicacion FastAPI: arma todo (rutas, cache, metricas, websocket) en un solo lugar."""
import asyncio
import time

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from src.api.routes import earthquakes, health, metrics, reports, websocket
from src.config.logging import get_logger
from src.config.settings import settings
from src.database.indexes import create_indexes
from src.utils.cache import SimpleCache

logger = get_logger("api.main")

app = FastAPI(
    title="Earthquake Real-Time Platform",
    description="Prueba tecnica Quipux: ingesta, procesamiento y reportes de sismos (USGS).",
    version="1.0.0",
)

HTTP_REQUESTS = Counter(
    "api_http_requests_total", "Cantidad de requests a la API", ["method", "path", "status_code"]
)
HTTP_REQUEST_DURATION = Histogram(
    "api_http_request_duration_seconds", "Duracion de cada request", ["method", "path"]
)


@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time

    HTTP_REQUESTS.labels(request.method, request.url.path, response.status_code).inc()
    HTTP_REQUEST_DURATION.labels(request.method, request.url.path).observe(duration)

    return response


@app.on_event("startup")
def on_startup():
    create_indexes()
    app.state.cache = SimpleCache(ttl_seconds=settings.cache_ttl_seconds)
    asyncio.create_task(websocket.broadcast_new_earthquakes_loop())
    logger.info("API iniciada correctamente")


@app.get("/observability/metrics")
def prometheus_metrics():
    """Endpoint que Prometheus consulta para leer las metricas de esta API."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(health.router, tags=["health"])
app.include_router(earthquakes.router, tags=["earthquakes"])
app.include_router(metrics.router, tags=["metrics"])
app.include_router(reports.router, tags=["reports"])
app.include_router(websocket.router, tags=["websocket"])
