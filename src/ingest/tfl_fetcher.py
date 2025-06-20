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


def main() -> None:
    data = asyncio.run(fetch())
    # show one station so we don't flood the terminal
    print(json.dumps(data[:1], indent=2))


if __name__ == "__main__":
    main()
