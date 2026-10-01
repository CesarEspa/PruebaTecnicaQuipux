"""Funciones pequenas para dejar los documentos de Mongo listos para responder por la API."""
from datetime import datetime


def serialize_doc(doc: dict) -> dict:
    """Convierte el _id (ObjectId) y las fechas de un documento de Mongo a texto, para mandarlo como JSON."""
    doc = dict(doc)
    for key, value in doc.items():
        if key == "_id":
            doc[key] = str(value)
        elif isinstance(value, datetime):
            doc[key] = value.isoformat()
    return doc
