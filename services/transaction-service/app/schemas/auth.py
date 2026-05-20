import uuid

from pydantic import BaseModel


class AuthUser(BaseModel):
    id: uuid.UUID | None = None
    first_name: str = ""
    last_name: str = ""


class AuthMeResponse(BaseModel):
    user: AuthUser
