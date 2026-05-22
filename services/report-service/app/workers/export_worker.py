import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from redis.asyncio import Redis

from app.cache import DashboardCache
from app.core.config import get_settings
from app.db.session import create_engine, create_sessionmaker
from app.models import ReportFile
from app.repositories.reports import ReportRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def process_export_message(message: AbstractIncomingMessage, sessionmaker) -> None:
    async with message.process(requeue=False):
        payload = json.loads(message.body.decode("utf-8"))
        job_id = uuid.UUID(payload["export_job_id"])
        async with sessionmaker() as session:
            repo = ReportRepository(session)
            job = await repo.get_export_job_by_id(job_id)
            if job is None:
                logger.warning("export job not found", extra={"job_id": str(job_id)})
                return
            try:
                now = datetime.now(timezone.utc)
                await repo.mark_export_job_processing(job, now)
                snapshot = job.report_snapshot
                content = json.dumps(
                    {
                        "report_snapshot_id": str(snapshot.id),
                        "report_type": snapshot.report_type,
                        "year": snapshot.year,
                        "month": snapshot.month,
                        "summary": {
                            "total_income": str(snapshot.total_income),
                            "total_expense": str(snapshot.total_expense),
                            "balance": str(snapshot.balance),
                            "savings_rate": str(snapshot.savings_rate),
                        },
                    }
                )
                file = ReportFile(
                    export_job_id=job.id,
                    file_url=f"memory://reports/{job.id}.{job.export_type.lower()}",
                    file_name=f"{snapshot.report_type.lower()}-{snapshot.year}-{snapshot.month or 'all'}.{job.export_type.lower()}",
                    file_type=job.export_type,
                    file_size=len(content.encode("utf-8")),
                )
                await repo.mark_export_job_completed(job, datetime.now(timezone.utc), file)
                await session.commit()
            except Exception as exc:
                await session.rollback()
                async with sessionmaker() as retry_session:
                    retry_repo = ReportRepository(retry_session)
                    retry_job = await retry_repo.get_export_job_by_id(job_id)
                    if retry_job is not None:
                        await retry_repo.mark_export_job_failed(
                            retry_job,
                            datetime.now(timezone.utc),
                            str(exc),
                        )
                        await retry_session.commit()
                raise


async def process_transaction_event(message: AbstractIncomingMessage, cache: DashboardCache) -> None:
    async with message.process(requeue=False):
        payload = json.loads(message.body.decode("utf-8"))
        user_id = payload.get("user_id")
        if user_id:
            deleted = await cache.invalidate_user(user_id)
            logger.info("invalidated dashboard cache", extra={"user_id": user_id, "deleted": deleted})


async def main() -> None:
    settings = get_settings()
    engine = create_engine(settings)
    sessionmaker = create_sessionmaker(engine)
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    cache = DashboardCache(redis, settings)
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            settings.rabbitmq_exchange,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        export_queue = await channel.declare_queue(settings.report_export_queue, durable=True)
        await export_queue.bind(exchange, routing_key="report.export.requested")
        await export_queue.consume(lambda message: process_export_message(message, sessionmaker))

        transaction_queue = await channel.declare_queue(settings.report_transaction_events_queue, durable=True)
        await transaction_queue.bind(exchange, routing_key="transaction.*")
        await transaction_queue.consume(lambda message: process_transaction_event(message, cache))

        logger.info("report worker started")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
