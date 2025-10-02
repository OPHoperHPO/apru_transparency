from django.conf import settings
import boto3
def _client():
    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )
def presign_put(key: str, content_type: str | None = None, expires: int = 3600) -> str:
    params = {"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key}
    if content_type:
        params["ContentType"] = content_type
    return _client().generate_presigned_url("put_object", Params=params, ExpiresIn=expires)
def presign_get(key: str, expires: int = 3600) -> str:
    params = {"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key}
    return _client().generate_presigned_url("get_object", Params=params, ExpiresIn=expires)
