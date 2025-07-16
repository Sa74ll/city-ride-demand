# src/etl/load_one.py
import asyncio
import datetime as dt
import io
import json
from typing import List, Tuple

import aioboto3
import psycopg

BUCKET = "raw-bike-status"
S3 = dict(
    endpoint_url="http://localhost:9000",
    aws_access_key_id="minio",
    aws_secret_access_key="minio123",
)
PG_DSN = "postgresql://tsadmin:tspass@localhost:5432/bikedb"


def flatten(rec: dict, ts: str) -> Tuple[dt.datetime, str, int, int]:
    props = {p["key"]: p["value"] for p in rec["additionalProperties"]}
    return (
        dt.datetime.fromisoformat(ts.replace("Z", "+00:00")),
        rec["id"],
        int(props["NbBikes"]),
        int(props["NbDocks"]),
    )


async def newest_key() -> str:
    session = aioboto3.Session()
    async with session.client("s3", **S3) as s3:
        pages = []
        paginator = s3.get_paginator("list_objects_v2")
        async for page in paginator.paginate(Bucket=BUCKET):
            pages.extend(page.get("Contents", []))
    if not pages:
        raise RuntimeError("Bucket is empty")
    return max(pages, key=lambda o: o["LastModified"])["Key"]


async def download_json(key: str) -> List[dict]:
    session = aioboto3.Session()
    async with session.client("s3", **S3) as s3:
        obj = await s3.get_object(Bucket=BUCKET, Key=key)
        raw = await obj["Body"].read()
    return json.loads(raw)


async def copy_rows(rows: List[Tuple]) -> None:
    async with await psycopg.AsyncConnection.connect(PG_DSN) as conn:
        async with conn.cursor() as cur:
            buf = io.StringIO()
            for r in rows:
                buf.write("\t".join(map(str, r)) + "\n")
            buf.seek(0)

            async with cur.copy(
                "COPY station_status (ts, station_id, bikes_free, docks_free) FROM STDIN"
            ) as copy:
                await copy.write(buf.read())

        await conn.commit()


async def load_latest_snapshot() -> None:
    key = await newest_key()
    print(f"Downloading {key!r} ...")

    data = await download_json(key)
    timestamp = key.split("/")[-1][:15]  # works with or without folder prefix
    rows = [flatten(r, timestamp) for r in data]

    await copy_rows(rows)
    print(f"✔ inserted {len(rows)} rows from {key}")


if __name__ == "__main__":
    asyncio.run(load_latest_snapshot())
