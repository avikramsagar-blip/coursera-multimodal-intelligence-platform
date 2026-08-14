import os
from typing import Optional
from urllib.parse import urljoin


class ObjectStorageService:
    def __init__(self):
        self.provider = os.getenv("OBJECT_STORAGE_PROVIDER", "local").lower()
        self.bucket_name = os.getenv("AWS_S3_BUCKET") or os.getenv("OBJECT_STORAGE_BUCKET")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.endpoint_url = os.getenv("AWS_ENDPOINT_URL") or os.getenv("S3_ENDPOINT_URL")
        self.public_base_url = os.getenv("AWS_S3_PUBLIC_URL") or os.getenv("OBJECT_STORAGE_PUBLIC_URL")

        # Local uploads root: default to <this file's dir>/uploads
        self._local_root = os.getenv(
            "LOCAL_UPLOAD_DIR",
            os.path.join(os.path.dirname(__file__), "uploads"),
        )

        if self.provider == "s3":
            import boto3
            from botocore.config import Config

            self.client = boto3.client(
                "s3",
                region_name=self.region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                config=Config(signature_version="s3v4"),
            )
        elif self.provider == "local":
            os.makedirs(self._local_root, exist_ok=True)
        else:
            raise ValueError(f"Unsupported object storage provider: {self.provider}")

    def _object_key(self, folder: str, filename: str) -> str:
        folder = folder.strip("/")
        filename = filename.strip("/")
        return f"{folder}/{filename}" if folder else filename

    # ------------------------------------------------------------------
    # Local helpers
    # ------------------------------------------------------------------

    def _local_path(self, object_key: str) -> str:
        """Absolute filesystem path for an object key inside the local root."""
        # Flatten the key into the uploads directory so every file lives under
        # /uploads/<key>, e.g. /uploads/course_1/materials/abc_file.pdf
        return os.path.join(self._local_root, object_key)

    def _local_url(self, object_key: str) -> str:
        """Return a server-relative URL that maps to the /uploads static mount."""
        return f"/uploads/{object_key}"

    # ------------------------------------------------------------------
    # Public API (same signature for both providers)
    # ------------------------------------------------------------------

    def upload_bytes(
        self,
        file_name: str,
        content: bytes,
        folder: str = "uploads",
        content_type: str = "application/octet-stream",
    ) -> str:
        object_key = self._object_key(folder, file_name)

        if self.provider == "local":
            dest = self._local_path(object_key)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as fh:
                fh.write(content)
            return self._local_url(object_key)

        # S3 path
        if not self.bucket_name:
            raise RuntimeError("AWS_S3_BUCKET must be configured for object storage uploads.")

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

    def upload_file(
        self,
        file_name: str,
        file_path: str,
        folder: str = "uploads",
        content_type: Optional[str] = None,
    ) -> str:
        with open(file_path, "rb") as fh:
            payload = fh.read()
        return self.upload_bytes(file_name, payload, folder=folder, content_type=content_type or "application/octet-stream")

    def delete(self, key: str) -> None:
        if self.provider == "local":
            # key is the object_key portion (without leading slash)
            path = self._local_path(key.lstrip("/"))
            try:
                os.remove(path)
            except FileNotFoundError:
                pass
            return

        # S3 path
        if not self.bucket_name:
            return
        self.client.delete_object(Bucket=self.bucket_name, Key=key)


storage_service = ObjectStorageService()
