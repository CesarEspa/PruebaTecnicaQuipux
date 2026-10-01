# Imagen compartida por api, ingestion y consumer. docker-compose cambia
# el comando (CMD) para cada uno.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/

ENV PYTHONPATH=/app

CMD ["python", "-m", "src.entrypoints.run_ingestion"]
