"""
Conexion a MongoDB.

Creamos el MongoClient UNA sola vez por proceso (variable a nivel de
modulo) y lo reutilizamos en toda la app. pymongo ya maneja un pool de
conexiones internamente, asi que no hay que abrir/cerrar conexion en
cada request: eso es lo que pide el enunciado con "gestion eficiente
de conexiones".

Este modulo lee las variables de entorno directamente con os.getenv
(en vez de usar src.config.settings) a proposito: asi tambien lo puede
usar el DAG de Airflow sin tener que instalar pydantic-settings dentro
de la imagen de Airflow.
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
