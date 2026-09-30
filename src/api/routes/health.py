from fastapi import APIRouter

from src.database.mongodb import get_db

router = APIRouter()


@router.get("/health")
def health_check():
    """Revisa que la API pueda hablar con MongoDB. Util para docker-compose healthcheck."""
    try:
        get_db().command("ping")
        return {"status": "ok", "mongodb": "connected"}
    except Exception as error:
        return {"status": "error", "mongodb": str(error)}
