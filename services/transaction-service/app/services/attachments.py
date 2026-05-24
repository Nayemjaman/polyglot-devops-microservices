import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Attachment
from app.services.exceptions import NotFoundError
from app.services.transactions import get_transaction


async def list_attachments(
    session: AsyncSession,
    user_id: uuid.UUID,
    transaction_id: uuid.UUID,
) -> list[Attachment]:
    transaction = await get_transaction(session, user_id, transaction_id)
    return transaction.attachments


async def create_attachment_record(
    session: AsyncSession,
    user_id: uuid.UUID,
    transaction_id: uuid.UUID,
    file_url: str,
    file_type: str,
    file_name: str,
) -> Attachment:
    await get_transaction(session, user_id, transaction_id)
    attachment = Attachment(
        transaction_id=transaction_id,
        file_url=file_url,
        file_type=file_type,
        file_name=file_name,
    )
    session.add(attachment)
    await session.commit()
    await session.refresh(attachment)
    return attachment


async def create_empty_attachment_record(
    session: AsyncSession,
    user_id: uuid.UUID,
    transaction_id: uuid.UUID,
    file_type: str,
    file_name: str,
) -> Attachment:
    await get_transaction(session, user_id, transaction_id)
    attachment = Attachment(
        transaction_id=transaction_id,
        file_url="pending",
        file_type=file_type,
        file_name=file_name,
    )
    session.add(attachment)
    await session.flush()
    return attachment


async def save_attachment_url(
    session: AsyncSession, attachment: Attachment, file_url: str
) -> Attachment:
    attachment.file_url = file_url
    await session.commit()
    await session.refresh(attachment)
    return attachment


async def delete_attachment(
    session: AsyncSession,
    user_id: uuid.UUID,
    transaction_id: uuid.UUID,
    attachment_id: uuid.UUID,
) -> Attachment:
    await get_transaction(session, user_id, transaction_id)
    attachment = await session.get(Attachment, attachment_id)
    if attachment is None or attachment.transaction_id != transaction_id:
        raise NotFoundError("Attachment not found")
    await session.delete(attachment)
    await session.commit()
    return attachment
