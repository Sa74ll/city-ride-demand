import asyncio
import datetime as dt
import io
import json
import sys
from typing import List, Tuple

import aiohttp
import psycopg

# London coordinates
LAT, LON = 51.5072, -0.1276
PG_DSN = "postgresql://tsadmin:tspass@localhost:5432/bikedb"


def url_for(date: str) -> str:
    """Open-Meteo archive: returns yesterdays hourly obs."""
    return (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={LAT}&longitude={LON}"
        f"&start_date={date}&end_date={date}"
        "&hourly=temperature_2m,precipitation,wind_speed_10m"
        "&timezone=UTC"
    )


def to_rows(js: dict) -> List[Tuple]:
    hrs = js["hourly"]
    return [
        (
            dt.datetime.fromisoformat(hrs["time"][i]),
            round(hrs["temperature_2m"][i]),
            round(hrs["precipitation"][i] * 10),  # mm → 0.1 mm for SMALLINT
            round(hrs["wind_speed_10m"][i]),
        )
        for i in range(len(hrs["time"]))
    ]


async def fetch(date: str) -> List[Tuple]:
    async with aiohttp.ClientSession() as s:
        async with s.get(url_for(date)) as r:
            js = await r.json()
    return to_rows(js)


async def upsert(rows: List[Tuple]) -> None:
    if not rows:
        print("⚠️  No weather rows, nothing inserted")
        return
    async with await psycopg.AsyncConnection.connect(PG_DSN) as conn:
        async with conn.cursor() as cur:
            buf = io.StringIO("\n".join("\t".join(map(str, r)) for r in rows) + "\n")
            async with cur.copy(
                """
                COPY weather_hourly (ts, air_temp, precip_tenth_mm, wind_kph)
                FROM STDIN
                """
            ) as cp:
                await cp.write(buf.read())
        await conn.commit()
    print(f"✔ Inserted {len(rows)} weather rows")


async def main(day: str):
    rows = await fetch(day)
    await upsert(rows)


if __name__ == "__main__":
    day = (
        sys.argv[1]
        if len(sys.argv) > 1
        else (dt.date.today() - dt.timedelta(days=1)).isoformat()
    )
    asyncio.run(main(day))
