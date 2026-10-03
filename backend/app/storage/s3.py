from typing import Optional, Dict, Any
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from .base import ObjectStorage
from ..core.config import settings


class S3ObjectStorage(ObjectStorage):
    """
    S3-compatible Object Storage adapter (AWS S3, MinIO, Cloudflare R2).
    Enforces private-by-default access using short-lived presigned URLs.
    """
    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        bucket_name: Optional[str] = None,
        region_name: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
    ):
        self.bucket = bucket_name or settings.s3_bucket
        self.endpoint_url = endpoint_url or settings.s3_endpoint_url
        self.region = region_name or settings.s3_region

        session = boto3.Session()
        self.client = session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region,
            aws_access_key_id=access_key_id or settings.s3_access_key_id,
            aws_secret_access_key=secret_access_key or settings.s3_secret_access_key,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def create_upload_url(
        self,
        object_key: str,
        content_type: str,
        expires_in: Optional[int] = None,
        expires_in_seconds: Optional[int] = None,
    ) -> str:
        ttl = expires_in if expires_in is not None else (expires_in_seconds or settings.presigned_url_ttl_seconds)
        return self.client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": self.bucket,
                "Key": object_key,
                "ContentType": content_type,
            },
            ExpiresIn=ttl,
        )

    def create_download_url(
        self,
        object_key: str,
        expires_in: Optional[int] = None,
        expires_in_seconds: Optional[int] = None,
    ) -> str:
        ttl = expires_in if expires_in is not None else (expires_in_seconds or settings.presigned_url_ttl_seconds)
        return self.client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": self.bucket,
                "Key": object_key,
            },
            ExpiresIn=ttl,
        )

    def head_object(self, object_key: str) -> Optional[Dict[str, Any]]:
        try:
            res = self.client.head_object(Bucket=self.bucket, Key=object_key)
            return {
                "size_bytes": res.get("ContentLength"),
                "content_type": res.get("ContentType"),
                "etag": res.get("ETag"),
                "last_modified": res.get("LastModified"),
            }
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return None
            raise

    def delete_object(self, object_key: str) -> bool:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=object_key)
            return True
        except ClientError:
            return False

    def read_range(self, object_key: str, offset: int = 0, length: int = 4096) -> bytes:
        try:
            byte_range = f"bytes={offset}-{offset + length - 1}"
            res = self.client.get_object(Bucket=self.bucket, Key=object_key, Range=byte_range)
            return res["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
                raise FileNotFoundError(f"Storage object '{object_key}' not found in S3.")
            raise

    def upload_object(self, object_key: str, data: Any, content_type: Optional[str] = None) -> str:
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        if hasattr(data, "read"):
            self.client.upload_fileobj(data, self.bucket, object_key, ExtraArgs=extra_args)
        elif isinstance(data, (bytes, bytearray)):
            import io
            self.client.upload_fileobj(io.BytesIO(data), self.bucket, object_key, ExtraArgs=extra_args)
        else:
            import io
            self.client.upload_fileobj(io.BytesIO(str(data).encode("utf-8")), self.bucket, object_key, ExtraArgs=extra_args)
        return object_key

    def object_exists(self, object_key: str) -> bool:
        return self.head_object(object_key) is not None

    def get_object_bytes(self, object_key: str) -> bytes:
        try:
            res = self.client.get_object(Bucket=self.bucket, Key=object_key)
            return res["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
                raise FileNotFoundError(f"Storage object '{object_key}' not found in S3.")
            raise

