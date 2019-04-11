from aioresponses import aioresponses
import aiohttp
import pytest

from solardat.http import BASE_URL, _cache
from solardat.async_fetch import fetch_file, fetch_many


@pytest.fixture
def mock_rsps():
    with aioresponses() as mocked:
        yield mocked

@pytest.fixture
async def session():
    async with aiohttp.ClientSession() as session:
        yield session

@pytest.mark.usefixtures("clear_response_cache")
@pytest.mark.asyncio
class TestFetchFile(object):
    filepath = "download/Archive/SIRO1604.txt"
    station_id = 94249
    n_rows = 100

    async def test_mocked(self, mock_rsps, session, archival_data):
        mock_rsps.add(f"{BASE_URL}/{self.filepath}", "GET", body=archival_data)

        station_id, rows = await fetch_file(session, self.filepath)
        assert station_id == self.station_id
        assert len(rows) == self.n_rows

    async def test_caches_consumed_response(self, mock_rsps, session, archival_data):
        mock_rsps.add(f"{BASE_URL}/{self.filepath}", "GET", body=archival_data)

        await fetch_file(session, self.filepath)
        cached_response = _cache[self.filepath]
        assert cached_response.content

    async def test_external(self, session):
        station_id, rows = await fetch_file(session, self.filepath)
        assert station_id == self.station_id
        assert len(rows) >= self.n_rows

@pytest.mark.usefixtures("clear_response_cache")
@pytest.mark.asyncio
class TestFetchMany(object):
    filepaths = (
        "download/Archive/SIRF1601.txt",
        "download/Archive/SIRF1602.txt",
    )
    station_id = 94249
    n_rows = 100

    async def test_mocked(self, mock_rsps, session, archival_data):
        for filepath in self.filepaths:
            mock_rsps.add(f"{BASE_URL}/{filepath}", "GET", body=archival_data)

        results = await fetch_many(session, self.filepaths)
        filestems, station_ids, all_rows = zip(*results)
        assert filestems == ("SIRF1601", "SIRF1602")
        assert all(station_id == self.station_id for station_id in station_ids)
        assert all(len(rows) == self.n_rows for rows in all_rows)

    async def test_external(self, session):
        results = await fetch_many(session, self.filepaths)
        filestems, station_ids, all_rows = zip(*results)
        assert filestems == ("SIRF1601", "SIRF1602")
        assert all(station_id == self.station_id for station_id in station_ids)
        assert all(len(rows) >= self.n_rows for rows in all_rows)
