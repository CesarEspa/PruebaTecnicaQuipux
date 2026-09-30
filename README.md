# Earthquake Real-Time Platform

Prueba técnica **Quipux** — Plataforma de ingesta, procesamiento en tiempo real y
reportes de sismos, usando datos públicos del **USGS Earthquake Program**.

> Ver [`ARCHITECTURE.md`](ARCHITECTURE.md) para el diagrama de arquitectura completo,
> la justificación de las decisiones de modelado de datos y la propuesta de
> arquitectura analítica/ML (bonus Nivel 4).

## 1. ¿Qué hace este proyecto?

1. Un **servicio de ingesta** consulta la API pública de USGS cada 3 minutos y
   publica los sismos nuevos en RabbitMQ.
2. Un **servicio de procesamiento** (consumidor de RabbitMQ) guarda cada sismo
   en MongoDB y actualiza las métricas de esa hora en tiempo real.
3. Una **API REST** (FastAPI) expone los sismos, las métricas y los reportes,
   además de un WebSocket para recibir sismos nuevos en vivo.
4. Un **DAG de Airflow** corre cada hora, genera un reporte consolidado y lo
   guarda en MongoDB (y una copia en Parquet).
5. **Prometheus + Grafana** muestran métricas de los servicios en un dashboard.

Todo corre con Docker Compose, sin necesidad de instalar Python localmente.

## 2. Requisitos

- Docker Desktop (con Docker Compose v2, viene incluido).
- Puertos libres en tu máquina: `8000`, `8080`, `9090`, `3000`, `15672`, `27017`, `5672`.

## 3. Cómo levantar el proyecto

```bash
# 1. Copia el archivo de variables de entorno de ejemplo
cp .env.example .env

# 2. Levanta todo (la primera vez construye las imagenes, tarda unos minutos)
docker compose up --build
```

Cuando todo esté arriba vas a tener disponible:

| Servicio                    | URL                                      | Notas |
|------------------------------|-------------------------------------------|-------|
| API (Swagger/OpenAPI)         | http://localhost:8000/docs                | Documentación interactiva |
| WebSocket de sismos en vivo    | ws://localhost:8000/ws/earthquakes        | Prueba desde Postman ("New > WebSocket Request") |
| Airflow                      | http://localhost:8080                     | Usuario/clave: ver sección 6 |
| RabbitMQ (panel admin)        | http://localhost:15672                    | Usuario/clave: los de tu `.env` |
| Prometheus                   | http://localhost:9090                     | |
| Grafana                      | http://localhost:3000                     | Usuario/clave: los de `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD` en `.env` |

Para bajar todo:

```bash
docker compose down
# Si tambien quieres borrar los datos guardados (Mongo, Grafana, Airflow):
docker compose down -v
```

## 4. Endpoints principales de la API

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/earthquakes` | Lista sismos. Filtros: `min_magnitude`, `max_magnitude`, `location`. Paginación: `page`, `page_size`. Orden: `sort_by` (`event_time` \| `magnitude`), `order` (`asc` \| `desc`) |
| GET | `/earthquakes/{event_id}` | Detalle de un sismo |
| GET | `/metrics` | Métricas por hora (paginado), o `?window=2026-06-17T10` para una hora específica |
| GET | `/metrics/current` | Métricas de la hora actual |
| GET | `/reports` | Reportes horarios generados por Airflow (paginado) |
| GET | `/health` | Chequeo de salud (verifica conexión a Mongo) |
| GET | `/observability/metrics` | Métricas en formato Prometheus |
| WS | `/ws/earthquakes` | Sismos nuevos en tiempo real |

Ejemplos completos en la colección de Postman: [`postman/earthquake-platform.postman_collection.json`](postman/earthquake-platform.postman_collection.json)
(importarla en Postman; la variable `baseUrl` ya viene configurada a `http://localhost:8000`).

## 5. Variables de entorno

Ver [`.env.example`](.env.example). Ninguna credencial viene "quemada" en el código:
todo se lee desde variables de entorno (usuario/clave de Mongo, RabbitMQ y Grafana).

## 6. Airflow: usuario y contraseña

`airflow standalone` (el modo que usamos, pensado para desarrollo) crea un
usuario admin con una contraseña aleatoria en el primer arranque. Para verla:

```bash
docker compose logs airflow | grep -i password
```

El DAG se llama `hourly_earthquake_report` y corre automáticamente cada hora
(`schedule="@hourly"`). También se puede disparar manualmente desde la UI de
Airflow con el botón ▶ para no tener que esperar una hora completa.

## 7. Cómo probar que todo funciona (flujo de punta a punta)

1. `docker compose logs -f ingestion` — deberías ver logs cada 3 minutos con
   la cantidad de sismos recibidos/nuevos.
2. `docker compose logs -f consumer` — deberías ver "Sismo ... guardado
   correctamente" poco después de cada ciclo de ingesta.
3. `curl http://localhost:8000/earthquakes` — deberías ver los sismos guardados.
4. `curl http://localhost:8000/metrics/current` — métricas de la hora actual.
5. En Airflow, ejecuta manualmente el DAG `hourly_earthquake_report` y luego
   `curl http://localhost:8000/reports` para ver el reporte generado.
6. Abre Grafana (`http://localhost:3000`) → dashboard **"Earthquake Platform -
   Overview"** (ya viene provisionado automáticamente).

> Nota: la API pública de USGS (`all_hour.geojson`) solo trae sismos si
> realmente ocurrieron en la última hora a nivel mundial. Si el feed viene
> vacío en el momento de la prueba, es comportamiento normal de la API, no un
> error del proyecto — el sistema simplemente no tendrá eventos nuevos que
> procesar hasta que ocurra un sismo real.

## 8. Estructura del proyecto

```
src/
├── deploy/Dockerfile          # imagen compartida por api / ingestion / consumer
├── config/                    # settings, logging, constantes
├── metadata/                  # schemas (validación Pydantic) y validators (parseo USGS)
├── models/                    # modelos Pydantic (earthquake, metric, report)
├── database/                  # conexión Mongo e índices
├── messaging/                 # publisher/consumer de RabbitMQ
├── clients/                   # cliente HTTP de USGS
├── services/                  # lógica de negocio (ingesta, procesamiento, métricas, reportes)
├── api/                       # FastAPI (rutas + main.py)
├── airflow/dags/              # DAG de Airflow
├── entrypoints/                # scripts que arrancan cada contenedor
└── utils/                     # cache, ventanas de tiempo, serializadores

airflow/                       # Dockerfile de Airflow (imagen oficial + pymongo/pandas/pyarrow)
monitoring/                    # configuración de Prometheus y Grafana
postman/                       # colección de Postman
data/lake/                     # salida de los Parquet generados por Airflow (bonus Nivel 4)
```

## 9. Bonificaciones implementadas

- **Nivel 1**: Pydantic (modelos y validación de query params), logging
  estructurado en JSON, separación de responsabilidades por carpetas, un solo
  `MongoClient` reutilizado (pool de conexiones), cache en memoria con TTL
  para `/metrics` y `/reports`.
- **Nivel 2**: Prometheus (métricas propias en ingestion, consumer y api) +
  Grafana con dashboard provisionado automáticamente.
- **Nivel 3**: RabbitMQ para desacoplar ingesta de procesamiento (arquitectura
  orientada a eventos) + WebSocket para push de sismos nuevos en tiempo real.
- **Nivel 4**: ver [`ARCHITECTURE.md`](ARCHITECTURE.md) — propuesta de
  arquitectura de datos analítica/ML, con una prueba de concepto real
  (exportación de eventos a Parquet en cada corrida del DAG).

## 10. Supuestos

Siguiendo el enunciado, **no se implementó**: autenticación, autorización,
frontend, despliegue en la nube, ni CI/CD.
