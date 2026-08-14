import os
from typing import BinaryIO, Optional
from urllib.parse import urljoin

import boto3
from botocore.config import Config


class ObjectStorageService:
    def __init__(self):
        self.provider = os.getenv("OBJECT_STORAGE_PROVIDER", "s3").lower()
        self.bucket_name = os.getenv("AWS_S3_BUCKET") or os.getenv("OBJECT_STORAGE_BUCKET")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.endpoint_url = os.getenv("AWS_ENDPOINT_URL") or os.getenv("S3_ENDPOINT_URL")
        self.public_base_url = os.getenv("AWS_S3_PUBLIC_URL") or os.getenv("OBJECT_STORAGE_PUBLIC_URL")

        if self.provider == "s3":
            self.client = boto3.client(
                "s3",
                region_name=self.region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                config=Config(signature_version="s3v4"),
            )
        else:
            raise ValueError(f"Unsupported object storage provider: {self.provider}")

    def _object_key(self, folder: str, filename: str) -> str:
        folder = folder.strip("/")
        filename = filename.strip("/")
        return f"{folder}/{filename}" if folder else filename

    def upload_bytes(self, file_name: str, content: bytes, folder: str = "uploads", content_type: str = "application/octet-stream") -> str:
        if not self.bucket_name:
            raise RuntimeError("AWS_S3_BUCKET must be configured for object storage uploads.")

        object_key = self._object_key(folder, file_name)
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=object_key,
            Body=content,
            ContentType=content_type,
            ACL="public-read",
        )

        if self.public_base_url:
            return urljoin(self.public_base_url.rstrip("/") + "/", object_key)

        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{object_key}"

    def upload_file(self, file_name: str, file_path: str, folder: str = "uploads", content_type: Optional[str] = None) -> str:
        with open(file_path, "rb") as file_handle:
            payload = file_handle.read()
        return self.upload_bytes(file_name, payload, folder=folder, content_type=content_type or "application/octet-stream")

    def delete(self, key: str) -> None:
        if not self.bucket_name:
            return
        self.client.delete_object(Bucket=self.bucket_name, Key=key)


storage_service = ObjectStorageService()
