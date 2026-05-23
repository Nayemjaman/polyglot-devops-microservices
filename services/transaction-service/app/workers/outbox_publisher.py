import asyncio
import logging

from app.core.config import get_settings
from app.db.session import create_engine, create_sessionmaker
from app.messaging import RabbitMQPublisher
from app.services import outbox as outbox_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def publish_batch(sessionmaker, publisher: RabbitMQPublisher, batch_size: int, max_attempts: int) -> int:
    async with sessionmaker() as session:
        events = await outbox_service.get_publishable_events(session, batch_size)
        for event in events:
            try:
                await publisher.publish(event.routing_key, event.payload, message_id=str(event.id))
                outbox_service.mark_published(event)
                logger.info("published outbox event", extra={"event_id": str(event.id), "routing_key": event.routing_key})
            except Exception as exc:
                outbox_service.mark_failed(event, exc, max_attempts)
                logger.exception("failed to publish outbox event", extra={"event_id": str(event.id)})
        await session.commit()
        return len(events)


async def main() -> None:
    settings = get_settings()
    engine = create_engine(settings)
    sessionmaker = create_sessionmaker(engine)
    publisher = RabbitMQPublisher(settings)
    await publisher.connect()
    logger.info("transaction outbox publisher started")
    try:
        while True:
            published = await publish_batch(
                sessionmaker,
                publisher,
                settings.outbox_batch_size,
                settings.outbox_max_attempts,
            )
            await asyncio.sleep(0 if published else settings.outbox_poll_interval_seconds)
    finally:
        await publisher.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
