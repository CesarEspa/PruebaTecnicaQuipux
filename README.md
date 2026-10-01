# Earthquake Real-Time Platform

Prueba técnica para Quipux: una plataforma que consume los sismos que publica el
USGS (United States Geological Survey), los guarda en MongoDB, calcula métricas
en tiempo real y genera reportes por hora con Airflow.

El diagrama de arquitectura y la explicación de las decisiones de diseño (por qué
Mongo, por qué RabbitMQ, etc.) están en [ARCHITECTURE.md](ARCHITECTURE.md).

## Qué hace

- Cada 3 minutos, un servicio revisa la API de USGS y publica los sismos nuevos en RabbitMQ.
- Otro servicio escucha esa cola, guarda cada sismo en MongoDB y actualiza las métricas de esa hora.
- Una API hecha con FastAPI expone esos datos (sismos, métricas, reportes) y también tiene un WebSocket que avisa cuando llega un sismo nuevo.
- Un DAG de Airflow corre cada hora, arma un reporte con lo que pasó esa hora y lo guarda en Mongo (más una copia en Parquet).
- Prometheus y Grafana muestran si los servicios están funcionando bien.

Todo se levanta con Docker Compose, no hace falta instalar Python en tu máquina.

## Requisitos

- Docker Desktop instalado y corriendo.
- Que estos puertos estén libres: 8000, 8080, 9090, 3000, 15672, 27017 y 5672.

## Cómo levantarlo

```bash
cp .env.example .env
docker compose up --build
```

La primera vez tarda varios minutos porque descarga las imágenes de Mongo, RabbitMQ, Airflow, etc. y construye las nuestras. Cuando se calme el log, en otra terminal corre `docker compose ps` y revisa que todos digan "Up".

Con todo arriba, esto es lo que puedes abrir:

- http://localhost:8000/docs — la API, con una página para probar cada endpoint dando clic (Swagger).
- ws://localhost:8000/ws/earthquakes — el WebSocket, se puede probar desde Postman con "New > WebSocket Request".
- http://localhost:8080 — Airflow (usuario y contraseña se explican más abajo).
- http://localhost:15672 — panel de RabbitMQ (usuario y clave son los que pusiste en el `.env`).
- http://localhost:9090 — Prometheus.
- http://localhost:3000 — Grafana (usuario/clave: los de `GRAFANA_ADMIN_USER` y `GRAFANA_ADMIN_PASSWORD` del `.env`).

Para apagar todo:

```bash
docker compose down
```

Si además quieres borrar los datos guardados (Mongo, Grafana, Airflow) y empezar de cero:

```bash
docker compose down -v
```

## Endpoints de la API

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/earthquakes` | Lista los sismos guardados. Admite filtros (`min_magnitude`, `max_magnitude`, `location`), paginación (`page`, `page_size`) y orden (`sort_by`, `order`) |
| GET | `/earthquakes/{event_id}` | El detalle de un sismo |
| GET | `/metrics` | Las métricas por hora. Con `?window=2026-06-17T10` trae la de esa hora puntual |
| GET | `/metrics/current` | Las métricas de la hora actual |
| GET | `/reports` | Los reportes que arma Airflow cada hora |
| GET | `/health` | Para saber si la API puede hablar con Mongo |
| GET | `/observability/metrics` | Métricas en formato Prometheus |
| WS | `/ws/earthquakes` | Avisa cuando llega un sismo nuevo |

Hay una colección de Postman lista en [postman/earthquake-platform.postman_collection.json](postman/earthquake-platform.postman_collection.json), con la variable `baseUrl` ya apuntando a `http://localhost:8000`.

## Variables de entorno

Están todas en [.env.example](.env.example), sin ninguna clave quemada en el código: usuario/contraseña de Mongo, de RabbitMQ y de Grafana se leen del `.env`.

## Usuario y contraseña de Airflow

Airflow corre en modo `standalone` (pensado para desarrollo), y la primera vez que arranca crea un usuario `admin` con una contraseña aleatoria. Para verla:

```bash
docker compose logs airflow | grep -i password
```

El DAG se llama `hourly_earthquake_report` y está programado para correr cada hora. Si no quieres esperar, se puede disparar a mano desde la interfaz de Airflow con el botón de play.

## Cómo revisar que todo funciona

1. `docker compose logs -f ingestion` — cada 3 minutos debería aparecer una línea diciendo cuántos sismos trajo y cuántos eran nuevos.
2. `docker compose logs -f consumer` — poco después debería aparecer "Sismo ... guardado correctamente".
3. `curl http://localhost:8000/earthquakes` — ya deberían verse sismos guardados.
4. `curl http://localhost:8000/metrics/current` — las métricas de la hora.
5. Corre el DAG de Airflow manualmente y después pega `curl http://localhost:8000/reports` para ver el reporte que generó.
6. Entra a Grafana, el dashboard ya viene armado solo (no hay que configurar nada).

Algo a tener en cuenta: la API de USGS que usamos solo trae los sismos que pasaron en la última hora en todo el mundo. Si justo no hubo ningún sismo real cuando estás probando, el feed viene vacío — es normal, no es un error del proyecto.

## Estructura del proyecto

```
src/
├── deploy/Dockerfile    imagen que comparten api, ingestion y consumer
├── config/              settings, logging, constantes
├── metadata/            validacion de parametros y parseo de la respuesta de USGS
├── models/              modelos de Pydantic (sismo, metrica, reporte)
├── database/            conexion a Mongo e indices
├── messaging/           publicar/consumir de RabbitMQ
├── clients/             cliente HTTP de USGS
├── services/            la logica de negocio: ingesta, procesamiento, metricas, reportes
├── api/                 FastAPI (rutas y main.py)
├── airflow/dags/        el DAG
├── entrypoints/         los scripts que arrancan cada contenedor
└── utils/               cache, ventanas de tiempo, serializadores

airflow/        Dockerfile de Airflow (imagen oficial + pymongo/pandas/pyarrow)
monitoring/     configuracion de Prometheus y Grafana
postman/        la coleccion de Postman
data/lake/      aqui caen los Parquet que genera Airflow
```

## Cosas extra que agregué además de lo pedido

- Pydantic en todos los modelos y en la validación de los query params de la API.
- Logging en JSON en vez de texto plano.
- Una cache simple en memoria para no pegarle a Mongo en cada request de `/metrics` y `/reports`.
- Prometheus y Grafana, con métricas propias de cada servicio.
- RabbitMQ para que la ingesta y el guardado en Mongo no dependan directamente uno del otro.
- Un WebSocket para recibir sismos nuevos sin tener que estar refrescando.
- Una idea de cómo escalar esto hacia analítica/Machine Learning más adelante (está en ARCHITECTURE.md), con una prueba real: cada reporte horario también se exporta a un archivo Parquet.

## Qué no se implementó

Como dice el enunciado de la prueba, no hacía falta: autenticación, autorización, frontend, despliegue en la nube ni CI/CD.
