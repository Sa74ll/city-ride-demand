import asyncio
import json

import pytest
from aioresponses import aioresponses

from ingest.tfl_fetcher import URL, fetch  # URL is defined in tfl_fetcher.py


@pytest.mark.asyncio
async def test_fetch_happy_path():
    """fetch() returns raw station list and parses first record's id."""

    sample = [
        {
            "id": "123",
            "commonName": "Dock",
            "lat": 0,
            "lon": 0,
            "additionalProperties": [
                {"key": "NbBikes", "value": "5"},
                {"key": "NbDocks", "value": "10"},
            ],
        }
    ]

    with aioresponses() as mock:
        mock.get(URL, payload=sample)  # fake the TfL endpoint
        data = await fetch()  # call the real function

    assert data[0]["id"] == "123"  # happy-path assertion
