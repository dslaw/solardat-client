from datetime import date
from io import BytesIO
from zipfile import ZipFile
import pytest
import requests
import responses

from solardat.fetch import (
    fetch_compressed,
    fetch_file,
    find_compressed,
    find_files,
)
from solardat.http import BASE_URL
from solardat.search import LIST_FILES_PATH


@pytest.mark.usefixtures("clear_response_cache")
class TestFindFiles(object):
    @responses.activate
    def test_mocked(self, search_results_page):
        stations = ["Eugene", "Silver Lake"]
        start = date(2016, 1, 1)
        end = date(2016, 10, 1)
        expected = {
            "Eugene, OR": [
                f"{BASE_URL}/download/Archive/EUPF1602.txt",
                f"{BASE_URL}/download/Archive/EUPQ1610.txt",
                f"{BASE_URL}/download/Archive/EURO1604.txt",
            ],
            "Silver Lake, OR": [
                f"{BASE_URL}/download/Archive/SIRO1608.txt",
                f"{BASE_URL}/download/Archive/SIRO1609.txt",
                f"{BASE_URL}/download/Archive/SIRO1610.txt",
            ],
        }

        responses.add(
            responses.POST,
            f"{BASE_URL}/{LIST_FILES_PATH}",
            body=search_results_page
        )

        filepaths = find_files(start, end, stations)
        assert filepaths == expected

    def test_external(self):
        stations = ["Silver Lake"]
        start = end = date(2016, 1, 1)

        filepaths = find_files(start, end, stations)
        found_stations = list(filepaths.keys())
        assert found_stations == ["Silver Lake, OR"]
        assert len(filepaths["Silver Lake, OR"]) > 0

@pytest.mark.usefixtures("clear_response_cache")
class TestFetchFile(object):
    filepath = "download/Archive/SIRO1604.txt"
    station_id = 94249
    n_rows = 100

    @responses.activate
    def test_mocked(self, archival_data):
        responses.add(responses.GET, f"{BASE_URL}/{self.filepath}", body=archival_data)

        station_id, rows = fetch_file(self.filepath)
        assert station_id == self.station_id
        assert len(rows) == self.n_rows

    def test_external(self):
        station_id, rows = fetch_file(self.filepath)
        assert station_id == self.station_id
        assert len(rows) >= self.n_rows

@pytest.mark.usefixtures("clear_response_cache")
class TestFindCompressed(object):
    @responses.activate
    def test_mocked(self, search_results_page, prepared_download_page):
        expected_path = f"download/temp/33729216.zip"
        stations = ["Silver Lake"]
        start = end = date(2018, 1, 1)

        responses.add(
            responses.POST,
            f"{BASE_URL}/{LIST_FILES_PATH}",
            body=search_results_page
        )
        responses.add(
            responses.POST,
            f"{BASE_URL}/cgi-bin/CompressDataFiles.cgi",
            body=prepared_download_page
        )

        filepath = find_compressed(start, end, stations)
        assert filepath == expected_path

    def test_external(self):
        stations = ["Silver Lake"]
        start = end = date(2018, 1, 1)

        filepath = find_compressed(start, end, stations)
        response = requests.head(f"{BASE_URL}/{filepath}")
        assert response.ok
        assert response.headers["Content-Type"] == "application/zip"

def make_compressed(filestems, raw):
    with BytesIO() as buffer:
        with ZipFile(buffer, mode="w") as zf:
            for filestem in filestems:
                zf.writestr(f"{filestem}.txt", raw)

        compressed = buffer.getvalue()

    return compressed

@pytest.mark.usefixtures("clear_response_cache")
class TestFetchCompressed(object):
    @responses.activate
    def test_mocked(self, archival_data):
        expected_filestems = ("ABCD1604", "ABCD1605")
        compressed = make_compressed(expected_filestems, archival_data)
        filepath = "download/temp/12345.zip"
        responses.add(responses.GET, f"{BASE_URL}/{filepath}", body=compressed)

        filestems, station_ids, contents = zip(*fetch_compressed(filepath))
        assert filestems == expected_filestems
        assert all(station_id == 94249 for station_id in station_ids)
        assert all(len(rows) == 100 for rows in contents)

    def test_external(self):
        stations = ["Silver Lake"]
        start = end = date(2018, 1, 1)
        expected_filestems = ("SIRF1801", "SIRO1801")

        filepath = find_compressed(start, end, stations)
        filestems, station_ids, contents = zip(*fetch_compressed(filepath))
        assert filestems == expected_filestems
        assert all(station_id == 94249 for station_id in station_ids)
        assert all(len(rows) > 0 for rows in contents)
