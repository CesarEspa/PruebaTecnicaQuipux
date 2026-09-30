"""Valores fijos que se usan en varias partes del proyecto."""

# Nombres de las colecciones de Mongo
COLLECTION_EARTHQUAKES = "earthquakes"
COLLECTION_METRICS = "metrics"
COLLECTION_HOURLY_REPORTS = "hourly_reports"

# RabbitMQ: exchange tipo "fanout" que reparte cada evento nuevo a la cola
# de procesamiento (si mas adelante se agregan mas consumidores, solo hay
# que crear su cola y conectarla a este mismo exchange).
EXCHANGE_EARTHQUAKES = "earthquakes_exchange"
QUEUE_PROCESSING = "processing_queue"

# Rangos de magnitud usados para la metrica de "distribucion por rango".
# (definidos por el candidato, siguiendo la escala de USGS)
MAGNITUDE_RANGES = [
    ("micro", 0.0, 3.0),
    ("light", 3.0, 5.0),
    ("moderate", 5.0, 6.0),
    ("strong", 6.0, 7.0),
    ("major_or_more", 7.0, 15.0),
]
