"""Cloudflare R2 storage for generated audio; Postgres never stores binary blobs."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import boto3

from .config import Settings


class ObjectStorage:
    def __init__(self, settings: Settings) -> None:
        self._bucket = settings.r2_bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.r2_endpoint,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name="auto",
        )

    def upload_file(self, key: str, path: Path, content_type: str) -> dict:
        self._client.upload_file(
            str(path), self._bucket, key, ExtraArgs={"ContentType": content_type}
        )
        response = self._client.head_object(Bucket=self._bucket, Key=key)
        return {"key": key, "bytes": response["ContentLength"], "etag": response["ETag"]}

    def open(self, key: str) -> tuple[BinaryIO, int | None]:
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        return response["Body"], response.get("ContentLength")


def configured_object_storage(settings: Settings) -> ObjectStorage | None:
    values = (
        settings.r2_account_id, settings.r2_access_key_id,
        settings.r2_secret_access_key, settings.r2_bucket, settings.r2_endpoint,
    )
    if not any(values):
        return None
    if not all(values):
        raise ValueError("all five TEACHING_AGENT_R2_* values are required when R2 is enabled")
    return ObjectStorage(settings)
