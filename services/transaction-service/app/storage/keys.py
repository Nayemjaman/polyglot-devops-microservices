import re
import uuid


_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def build_attachment_object_key(
    *,
    prefix: str,
    user_id: uuid.UUID,
    transaction_id: uuid.UUID,
    attachment_id: uuid.UUID,
    filename: str,
) -> str:
    safe_filename = _UNSAFE_FILENAME_CHARS.sub("-", filename.strip()).strip(".-")
    if not safe_filename:
        safe_filename = "attachment"

    clean_prefix = prefix.strip("/")
    key_parts = [
        clean_prefix,
        str(user_id),
        "transactions",
        str(transaction_id),
        "attachments",
        str(attachment_id),
        safe_filename,
    ]
    return "/".join(part for part in key_parts if part)
