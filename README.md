# Earthquake Real-Time Platform

Primero que todo agradacerle por la oportunidad y por el tiempo de revisar mi perfil, mis proceso de seleccion, espero sea de su agrado y poder trabajar con ustedes. Un gusto Att: Magister Cesar Libardo España Salguero. 

Prueba técnica para Quipux. Ingesto los sismos que publica el USGS, los guardo en MongoDB, calculo métricas en tiempo real y genero un reporte por hora con Airflow. Todo corre con Docker Compose.

El diagrama de arquitectura y por qué elegí cada pieza están en [ARCHITECTURE.md](ARCHITECTURE.md).

## Cómo levantarlo

```bash
cp .env.example .env
docker compose up --build
```

La primera vez tarda unos minutos (descarga Mongo, RabbitMQ, Airflow, etc. y construye las imágenes nuestras). Cuando el log se calme, en otra terminal corre `docker compose ps` y espera a que todo diga "Up".

Con todo arriba:

- http://localhost:8000/docs — la API, se prueba dando clic, no hace falta Postman
- http://localhost:8000/dashboard — panel simple con sismos, métricas, reportes y un mapa
- ws://localhost:8000/ws/earthquakes — WebSocket con los sismos en vivo
- http://localhost:8080 — Airflow (usuario y clave, más abajo)
- http://localhost:15672 — panel de RabbitMQ
- http://localhost:9090 — Prometheus
- http://localhost:3000 — Grafana

Para apagar: `docker compose down` (agrégale `-v` si también quieres borrar los datos guardados).

## Endpoints

- `GET /earthquakes` — lista los sismos, con filtros, paginación y orden
- `GET /earthquakes/{event_id}` — el detalle de uno
- `GET /metrics` — métricas por hora
- `GET /metrics/current` — la de la hora actual
- `GET /reports` — los reportes que arma Airflow
- `GET /health` — si la API puede hablar con Mongo
- `WS /ws/earthquakes` — sismos nuevos en vivo

Colección de Postman lista en [postman/earthquake-platform.postman_collection.json](postman/earthquake-platform.postman_collection.json).

## Variables de entorno

Todas en [.env.example](.env.example). Nada de claves quemadas en el código.

## Usuario y contraseña de Airflow

Airflow corre en modo `standalone` y crea un admin con contraseña aleatoria la primera vez que arranca. Para verla:

```bash
docker compose logs airflow | grep -i password
```

El DAG se llama `hourly_earthquake_report` y corre solo cada hora. Si no quieres esperar, dale play manualmente desde la interfaz de Airflow.

## Para comprobar que funciona

1. `docker compose logs -f ingestion` — cada 3 minutos debería salir un resumen de sismos recibidos/nuevos
2. `curl http://localhost:8000/earthquakes` — ya deberían verse datos
3. Corre el DAG de Airflow y revisa `curl http://localhost:8000/reports`
4. Entra a Grafana, el dashboard ya está armado solo

Algo a tener en cuenta: la API del USGS solo trae los sismos de la última hora en todo el mundo. Si justo no pasó nada, el feed viene vacío — eso es normal, no un error.

## Estructura

```
src/
├── config/        settings, logging, constantes
├── metadata/      validacion de la API y parseo de USGS
├── models/        modelos de Pydantic
├── database/      conexion a Mongo e indices
├── messaging/     RabbitMQ
├── clients/       cliente de USGS
├── services/      la logica: ingesta, procesamiento, metricas, reportes
├── api/           FastAPI
├── airflow/dags/  el DAG
├── entrypoints/   scripts que arrancan cada contenedor
└── utils/         cache, fechas, serializadores

airflow/       Dockerfile de Airflow
monitoring/    config de Prometheus y Grafana
postman/       la coleccion
data/lake/     los Parquet que genera Airflow
```

## Qué agregué además de lo pedido

Pydantic en todo, logging en JSON, una cache simple para no saturar Mongo, Prometheus + Grafana, RabbitMQ para desacoplar la ingesta del guardado, un WebSocket en tiempo real, un dashboard simple en `/dashboard` para ver todo sin usar curl/Postman (tabla de sismos, métricas con gráficos, reportes y un mapa), y una idea de cómo escalar esto a analítica/ML (ver ARCHITECTURE.md) con una prueba real: cada hora se genera un Parquet además del reporte en Mongo.

## Qué no hice

No hacía falta: autenticación, autorización, frontend, nube ni CI/CD aunque decidi agregarle frontend con IA.
