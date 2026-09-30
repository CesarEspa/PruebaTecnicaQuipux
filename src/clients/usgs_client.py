"""Cliente simple para consultar la API publica de USGS."""
import requests

from src.config.logging import get_logger
from src.config.settings import settings

logger = get_logger("clients.usgs")


def fetch_latest_earthquakes() -> list[dict]:
    """
    Llama a la API de USGS y devuelve la lista de "features" (sismos).

    Si algo sale mal (timeout, error de red, respuesta invalida) se
    registra el error y se devuelve una lista vacia, para que el
    servicio de ingesta pueda seguir corriendo en el siguiente ciclo.
    """
    try:
        response = requests.get(settings.usgs_api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("features", [])
    except requests.RequestException as error:
        logger.error(f"Error consultando la API de USGS: {error}")
        return []
