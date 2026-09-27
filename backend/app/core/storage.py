import posixpath

import boto3

from backend.app.core.config import settings


class MinIOStorageService:
    """
    S3-compatible object storage service.

    Current production target:
    Backblaze B2 S3 API.

    The class name is retained for backward compatibility with existing imports.
    """

    def __init__(self):
        self.endpoint = settings.S3_ENDPOINT
        self.access_key = settings.S3_ACCESS_KEY
        self.secret_key = settings.S3_SECRET_KEY
        self.bucket = getattr(
            settings,
            "S3_BUCKET_REPORTS",
            getattr(settings, "S3_BUCKET_NAME", "agni-netra-reports"),
        )
        self.use_ssl = settings.S3_USE_SSL
        self.region_name = getattr(settings, "S3_REGION", "us-west-004")

        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region_name,
            use_ssl=self.use_ssl,
        )

    def check_health(self) -> dict:
        """
        Verify that the configured bucket is reachable.
        """
        try:
            self.client.head_bucket(Bucket=self.bucket)
            return {
                "status": "HEALTHY",
                "service": "Backblaze B2 S3 Object Storage",
                "endpoint": self.endpoint,
                "bucket": self.bucket,
            }
        except Exception as exc:
            return {
                "status": "UNHEALTHY",
                "service": "Backblaze B2 S3 Object Storage",
                "endpoint": self.endpoint,
                "bucket": self.bucket,
                "error": str(exc),
            }

    def save_file(
        self,
        file_path: str,
        data: bytes,
        content_type: str = "application/pdf",
    ) -> str:
        """
        Upload bytes to the reports bucket.

        Returns the private object key, not a public URL.
        """
        object_key = posixpath.normpath(file_path).lstrip("/")

        self.client.put_object(
            Bucket=self.bucket,
            Key=object_key,
            Body=data,
            ContentType=content_type,
        )

        return object_key

    def read_file(self, file_path: str) -> bytes:
        """
        Download an object from the reports bucket.
        """
        object_key = posixpath.normpath(file_path).lstrip("/")

        response = self.client.get_object(
            Bucket=self.bucket,
            Key=object_key,
        )

        return response["Body"].read()

    def file_exists(self, file_path: str) -> bool:
        """
        Check whether an object exists in the reports bucket.
        """
        object_key = posixpath.normpath(file_path).lstrip("/")

        try:
            self.client.head_object(
                Bucket=self.bucket,
                Key=object_key,
            )
            return True
        except Exception:
            return False

    def delete_file(self, file_path: str) -> None:
        """
        Delete an object from the reports bucket.
        """
        object_key = posixpath.normpath(file_path).lstrip("/")

        self.client.delete_object(
            Bucket=self.bucket,
            Key=object_key,
        )


storage_service = MinIOStorageService()
