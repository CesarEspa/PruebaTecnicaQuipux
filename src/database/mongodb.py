"""
Conexion a MongoDB. El MongoClient se crea una sola vez por proceso y se
reutiliza (pymongo ya maneja su propio pool de conexiones por dentro).

Usa os.getenv en vez de src.config.settings para que el DAG de Airflow
tambien pueda importar este archivo sin necesitar pydantic-settings.
"""
import os

from pymongo import MongoClient
from pymongo.database import Database

_client: MongoClient | None = None


def _build_mongo_uri() -> str:
    user = os.getenv("MONGO_USER", "admin")
    password = os.getenv("MONGO_PASSWORD", "admin123")
    host = os.getenv("MONGO_HOST", "localhost")
    port = os.getenv("MONGO_PORT", "27017")
    return f"mongodb://{user}:{password}@{host}:{port}/?authSource=admin"


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(_build_mongo_uri())
    return _client


def get_db() -> Database:
    db_name = os.getenv("MONGO_DB", "earthquakes_db")
    return get_client()[db_name]
