import asyncio
import json
from typing import Any, List

import aiohttp
from tenacity import retry, stop_after_attempt

URL = "https://api.tfl.gov.uk/BikePoint"


@retry(stop=stop_after_attempt(3))
async def fetch() -> List[Any]:
    """Fetch BikePoint stations (retries up to 3 times on failure)."""
    async with aiohttp.ClientSession() as session:
        async with session.get(URL, timeout=30) as resp:
            resp.raise_for_status()
            return await resp.json()


def to_gbfs(rec: dict) -> dict:
    """Convert one TfL station record to a simplified GBFS-style dict."""
    props = {p["key"]: p["value"] for p in rec["additionalProperties"]}
    return {
        "station_id": rec["id"],
        "name": rec["commonName"],
        "lat": rec["lat"],
        "lon": rec["lon"],
        "bikes": int(props["NbBikes"]),
        "docks": int(props["NbDocks"]),
    }


def main() -> None:
    data = asyncio.run(fetch())
    print(json.dumps(to_gbfs(data[0]), indent=2))


if __name__ == "__main__":
    main()
