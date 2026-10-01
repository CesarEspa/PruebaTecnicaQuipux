"""Valores fijos que se usan en varias partes del proyecto."""

COLLECTION_EARTHQUAKES = "earthquakes"
COLLECTION_METRICS = "metrics"
COLLECTION_HOURLY_REPORTS = "hourly_reports"

EXCHANGE_EARTHQUAKES = "earthquakes_exchange"
QUEUE_PROCESSING = "processing_queue"

# Rangos de magnitud para la metrica de distribucion (escala de USGS).
MAGNITUDE_RANGES = [
    ("micro", 0.0, 3.0),
    ("light", 3.0, 5.0),
    ("moderate", 5.0, 6.0),
    ("strong", 6.0, 7.0),
    ("major_or_more", 7.0, 15.0),
]
