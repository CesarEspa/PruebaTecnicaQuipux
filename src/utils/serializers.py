"""Funciones pequenas para dejar los documentos de Mongo listos para responder por la API."""
from datetime import datetime


def serialize_doc(doc: dict) -> dict:
    """
    Deja un documento de Mongo listo para mandarlo como JSON:
    - convierte el _id (ObjectId) a texto.
    - convierte cualquier campo de fecha (datetime) a texto ISO.

    Esto hace falta sobre todo para el WebSocket: a diferencia de las rutas
    HTTP normales de FastAPI (que ya convierten fechas automaticamente),
    WebSocket.send_json() usa el json.dumps de Python "de toda la vida",
    que no sabe convertir ObjectId ni datetime por su cuenta.
    """
    doc = dict(doc)
    for key, value in doc.items():
        if key == "_id":
            doc[key] = str(value)
        elif isinstance(value, datetime):
            doc[key] = value.isoformat()
    return doc
