"""
WebSocket para recibir sismos nuevos en tiempo real.

En vez de conectarlo directamente a RabbitMQ, cada pocos segundos
revisamos en Mongo si hay sismos mas nuevos que el ultimo que mandamos,
y si hay, se los avisamos a todos los clientes conectados.
"""
import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.config.constants import COLLECTION_EARTHQUAKES
from src.config.logging import get_logger
from src.database.mongodb import get_db
from src.utils.serializers import serialize_doc

router = APIRouter()
logger = get_logger("api.websocket")

POLL_INTERVAL_SECONDS = 5


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as error:
                logger.warning(f"No se pudo enviar el mensaje, se desconecta el cliente: {error}")
                self.disconnect(connection)


manager = ConnectionManager()


async def broadcast_new_earthquakes_loop():
    """Tarea de fondo que revisa Mongo y avisa a los clientes conectados."""
    last_seen_time = datetime.now(timezone.utc)

    while True:
        await asyncio.sleep(POLL_INTERVAL_SECONDS)

        if not manager.active_connections:
            continue

        db = get_db()
        cursor = db[COLLECTION_EARTHQUAKES].find(
            {"event_time": {"$gt": last_seen_time}}
        ).sort("event_time", 1)

        for doc in cursor:
            last_seen_time = doc["event_time"]
            await manager.broadcast(serialize_doc(doc))


@router.websocket("/ws/earthquakes")
async def websocket_earthquakes(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # solo para detectar si el cliente se desconecta
    except WebSocketDisconnect:
        manager.disconnect(websocket)
