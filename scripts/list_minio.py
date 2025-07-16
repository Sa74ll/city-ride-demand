import asyncio
import os

import aioboto3

BUCKET = "raw-bike-status"
S3 = dict(
    endpoint_url="http://localhost:9000",
    aws_access_key_id="minio",
    aws_secret_access_key="minio123",
)


async def main() -> None:
    session = aioboto3.Session()
    async with session.client("s3", **S3) as s3:
        paginator = s3.get_paginator("list_objects_v2")
        async for page in paginator.paginate(Bucket=BUCKET):
            for obj in page.get("Contents", []):
                print(obj["Key"])


if __name__ == "__main__":
    asyncio.run(main())
