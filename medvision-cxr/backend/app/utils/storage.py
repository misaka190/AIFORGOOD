from pathlib import Path

from minio import Minio
from urllib3 import PoolManager, Timeout
from minio.error import S3Error

from app.core.config import get_settings


class ObjectStorage:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.settings.local_storage_root.mkdir(parents=True, exist_ok=True)
        self.client = Minio(
            self.settings.minio_endpoint,
            access_key=self.settings.minio_access_key,
            secret_key=self.settings.minio_secret_key,
            secure=self.settings.minio_secure,
            http_client=PoolManager(timeout=Timeout(connect=1.0, read=2.0)),
        )

    def ensure_bucket(self, bucket_name: str) -> None:
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
        except Exception:
            local_bucket = self.settings.local_storage_root / bucket_name
            local_bucket.mkdir(parents=True, exist_ok=True)

    def put_bytes(self, bucket_name: str, object_name: str, data: bytes, content_type: str) -> str:
        self.ensure_bucket(bucket_name)
        try:
            import io

            self.client.put_object(bucket_name, object_name, io.BytesIO(data), length=len(data), content_type=content_type)
        except Exception:
            local_path = self.settings.local_storage_root / bucket_name / object_name
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(data)
        return object_name

    def get_bytes(self, bucket_name: str, object_name: str) -> bytes:
        try:
            response = self.client.get_object(bucket_name, object_name)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()
        except Exception:
            local_path = self.settings.local_storage_root / bucket_name / object_name
            if not local_path.exists():
                raise FileNotFoundError(f"Object not found: {bucket_name}/{object_name}")
            return local_path.read_bytes()

    def delete_object(self, bucket_name: str, object_name: str) -> None:
        try:
            self.client.remove_object(bucket_name, object_name)
            return
        except Exception:
            local_path = self.settings.local_storage_root / bucket_name / object_name
            if local_path.exists():
                local_path.unlink()

    def public_url(self, bucket_name: str, object_name: str) -> str:
        return f"/storage/{bucket_name}/{object_name}"


storage = ObjectStorage()
