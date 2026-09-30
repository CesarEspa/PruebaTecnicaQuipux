"""Funciones pequenas para dejar los documentos de Mongo listos para responder por la API."""


def serialize_doc(doc: dict) -> dict:
    """Convierte el _id de Mongo (ObjectId) a texto para que se pueda mandar como JSON."""
    doc = dict(doc)
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc
