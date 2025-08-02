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


def safe_round(val, factor=1):
    """Return int(round(val * factor)) or 0 if val is None."""
    if val is None:
        return 0
    return round(val * factor)


def to_rows(js: dict) -> List[Tuple]:
    hrs = js["hourly"]
    rows = []
    for i in range(len(hrs["time"])):
        rows.append(
            (
                dt.datetime.fromisoformat(hrs["time"][i]),
                safe_round(hrs["temperature_2m"][i]),
                safe_round(hrs["precipitation"][i], factor=10),  # 0.1 mm precision
                safe_round(hrs["wind_speed_10m"][i]),
            )
        )
    return rows


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
            # 1) create temp staging table
            await cur.execute(
                """
                CREATE TEMP TABLE _wx_stage (
                    ts TIMESTAMPTZ,
                    air_temp SMALLINT,
                    precip_tenth_mm SMALLINT,
                    wind_kph SMALLINT
                ) ON COMMIT DROP;
            """
            )

            # 2) COPY into the temp table
            buf = io.StringIO("\n".join("\t".join(map(str, r)) for r in rows) + "\n")
            async with cur.copy("COPY _wx_stage FROM STDIN") as cp:
                await cp.write(buf.read())

            # 3) Merge into the real hypertable (ignore duplicates)
            await cur.execute(
                """
                INSERT INTO weather_hourly
                SELECT * FROM _wx_stage
                ON CONFLICT (ts) DO UPDATE
                  SET air_temp = EXCLUDED.air_temp,
                      precip_tenth_mm = EXCLUDED.precip_tenth_mm,
                      wind_kph = EXCLUDED.wind_kph;
            """
            )

        await conn.commit()
    print(f"✔ Upserted {len(rows)} weather rows")


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
