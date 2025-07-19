import asyncio
import datetime as dt
import json
import os

import aioboto3
from botocore.exceptions import ClientError

from ingest.tfl_fetcher import fetch  # your async fetcher

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minio")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minio123")
BUCKET = "raw-bike-status"


async def ensure_bucket(s3, name: str) -> None:

    try:
        await s3.head_bucket(Bucket=name)
    except ClientError as exc:
        # MinIO returns 404, AWS returns 404 with 'NoSuchBucket' code
        err_code = exc.response.get("Error", {}).get("Code", "")
        if err_code in ("404", "NoSuchBucket"):
            await s3.create_bucket(Bucket=name)
        else:
            raise


async def dump_once() -> None:
    """Fetch TfL data and upload one JSON snapshot to MinIO."""
    session = aioboto3.Session()
    async with session.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
    ) as s3:
        # make sure bucket exists *before* we upload
        await ensure_bucket(s3, BUCKET)

        timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        body = json.dumps(await fetch()).encode()

        await s3.put_object(
            Bucket=BUCKET,
            Key=f"{timestamp}.json",
            Body=body,
            ContentType="application/json",
        )
        print(f"✅ wrote {timestamp}.json")


if __name__ == "__main__":
    asyncio.run(dump_once())
