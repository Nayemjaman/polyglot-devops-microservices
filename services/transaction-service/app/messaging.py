import json
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import aio_pika
from aio_pika.abc import AbstractChannel, AbstractConnection, AbstractExchange

from app.core.config import Settings

logger = logging.getLogger(__name__)


def json_default(value: Any) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    return str(value)


class RabbitMQPublisher:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.connection: AbstractConnection | None = None
        self.channel: AbstractChannel | None = None
        self.exchange: AbstractExchange | None = None

    async def connect(self) -> None:
        self.connection = await aio_pika.connect_robust(self.settings.rabbitmq_url)
        self.channel = await self.connection.channel()
        self.exchange = await self.channel.declare_exchange(
            self.settings.rabbitmq_exchange,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

    async def close(self) -> None:
        if self.connection:
            await self.connection.close()

    async def publish(
        self, routing_key: str, payload: dict[str, Any], message_id: str | None = None
    ) -> None:
        if self.exchange is None:
            return
        await self.exchange.publish(
            aio_pika.Message(
                body=json.dumps(payload, default=json_default).encode("utf-8"),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                message_id=message_id,
            ),
            routing_key=routing_key,
        )


class NullPublisher:
    async def publish(
        self, routing_key: str, payload: dict[str, Any], message_id: str | None = None
    ) -> None:
        logger.warning("RabbitMQ unavailable; skipped publish", extra={"routing_key": routing_key})
