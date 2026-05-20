from __future__ import annotations

from collections.abc import Mapping
from functools import partial
from typing import Any

import anyio
import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import Settings


class StorageUnavailableError(RuntimeError):
    pass


class AttachmentStorage:
    def __init__(self, settings: Settings) -> None:
        self.bucket_name = settings.storage_bucket_name
        self.public_base_url = settings.storage_public_base_url
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.storage_endpoint_url,
            region_name=settings.storage_region,
            aws_access_key_id=settings.storage_access_key,
            aws_secret_access_key=settings.storage_secret_key,
            config=Config(signature_version="s3v4"),
        )

    async def check_bucket(self) -> None:
        try:
            await anyio.to_thread.run_sync(partial(self._client.head_bucket, Bucket=self.bucket_name))
        except (BotoCoreError, ClientError) as exc:
            raise StorageUnavailableError("attachment bucket unavailable") from exc

    async def create_presigned_put_url(
        self,
        object_key: str,
        content_type: str,
        expires_in_seconds: int = 900,
    ) -> str:
        params: Mapping[str, Any] = {
            "Bucket": self.bucket_name,
            "Key": object_key,
            "ContentType": content_type,
        }
        return await anyio.to_thread.run_sync(
            partial(
                self._client.generate_presigned_url,
                "put_object",
                Params=params,
                ExpiresIn=expires_in_seconds,
            )
        )

    async def upload_fileobj(self, fileobj: Any, object_key: str, content_type: str) -> None:
        await anyio.to_thread.run_sync(
            partial(
                self._client.upload_fileobj,
                fileobj,
                self.bucket_name,
                object_key,
                ExtraArgs={"ContentType": content_type},
            )
        )

    async def delete_object(self, object_key: str) -> None:
        await anyio.to_thread.run_sync(
            partial(self._client.delete_object, Bucket=self.bucket_name, Key=object_key)
        )

    def public_url(self, object_key: str) -> str:
        return f"{self.public_base_url}/{self.bucket_name}/{object_key.lstrip('/')}"
