# Imagen base compartida por los 3 servicios de Python: api, ingestion y consumer.
# docker-compose.yml usa la misma imagen para los tres y solo cambia el
# comando ("command") que se ejecuta al final.
FROM python:3.11-slim

WORKDIR /app

# Copiamos primero solo requirements.txt para aprovechar el cache de Docker:
# si el codigo cambia pero las dependencias no, no se vuelven a instalar.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/

ENV PYTHONPATH=/app

# Comando por defecto (docker-compose lo sobreescribe para cada servicio).
CMD ["python", "-m", "src.entrypoints.run_ingestion"]
