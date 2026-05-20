import uuid
from datetime import datetime

from app.schemas.base import ModelOut


class AttachmentOut(ModelOut):
    id: uuid.UUID
    transaction_id: uuid.UUID | None = None
    file_url: str
    file_type: str
    file_name: str
    uploaded_at: datetime
