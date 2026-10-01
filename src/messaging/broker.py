"""
Funciones para publicar y consumir mensajes de RabbitMQ con pika.

Se usa un exchange "fanout": el servicio de ingesta publica un sismo
nuevo ahi, y RabbitMQ lo reparte a las colas conectadas (hoy solo
processing_queue). Si despues se quiere agregar otro consumidor, solo
hay que crear su cola y conectarla, sin tocar la ingesta.
"""
import json

import pika

from src.config.constants import EXCHANGE_EARTHQUAKES, QUEUE_PROCESSING
from src.config.logging import get_logger
from src.config.settings import settings

logger = get_logger("messaging.broker")


def get_connection() -> pika.BlockingConnection:
    credentials = pika.PlainCredentials(
        settings.rabbitmq_user, settings.rabbitmq_password
    )
    parameters = pika.ConnectionParameters(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        credentials=credentials,
        heartbeat=30,
    )
    return pika.BlockingConnection(parameters)


def setup_exchange_and_queue(channel) -> None:
    """Crea el exchange y la cola si no existen (es seguro llamarlo varias veces)."""
    channel.exchange_declare(exchange=EXCHANGE_EARTHQUAKES, exchange_type="fanout", durable=True)
    channel.queue_declare(queue=QUEUE_PROCESSING, durable=True)
    channel.queue_bind(exchange=EXCHANGE_EARTHQUAKES, queue=QUEUE_PROCESSING)


def publish_earthquake_event(event_dict: dict) -> None:
    """Publica un sismo nuevo en el exchange (abre y cierra conexion en cada llamada, la ingesta solo publica cada 3 min)."""
    connection = get_connection()
    try:
        channel = connection.channel()
        setup_exchange_and_queue(channel)

        channel.basic_publish(
            exchange=EXCHANGE_EARTHQUAKES,
            routing_key="",
            body=json.dumps(event_dict, default=str),
            properties=pika.BasicProperties(delivery_mode=2),  # mensaje persistente
        )
        logger.info(f"Evento publicado en RabbitMQ: {event_dict.get('event_id')}")
    finally:
        connection.close()


def start_consuming(on_message_callback) -> None:
    """Se conecta a la cola y queda escuchando mensajes para siempre (bloquea el proceso)."""
    connection = get_connection()
    channel = connection.channel()
    setup_exchange_and_queue(channel)

    # Solo procesamos un mensaje a la vez antes de pedir el siguiente.
    channel.basic_qos(prefetch_count=1)

    def _wrapper(ch, method, properties, body):
        try:
            event_dict = json.loads(body)
            on_message_callback(event_dict)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as error:
            logger.error(f"Error procesando mensaje de RabbitMQ: {error}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_consume(queue=QUEUE_PROCESSING, on_message_callback=_wrapper)

    logger.info("Esperando mensajes en RabbitMQ...")
    channel.start_consuming()
