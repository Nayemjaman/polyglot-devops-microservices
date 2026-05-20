import uuid

from app.storage.keys import build_attachment_object_key


def test_build_attachment_object_key_uses_meaningful_safe_path() -> None:
    user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    transaction_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
    attachment_id = uuid.UUID("00000000-0000-0000-0000-000000000003")

    object_key = build_attachment_object_key(
        prefix="attachments",
        user_id=user_id,
        transaction_id=transaction_id,
        attachment_id=attachment_id,
        filename=" May receipt #1.pdf ",
    )

    assert object_key == (
        "attachments/00000000-0000-0000-0000-000000000001/"
        "transactions/00000000-0000-0000-0000-000000000002/"
        "attachments/00000000-0000-0000-0000-000000000003/"
        "May-receipt-1.pdf"
    )
