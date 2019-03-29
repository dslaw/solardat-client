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


# Duplicated from `test_search.py`
@pytest.fixture(scope="module")
def listing_content():
    with open("tests/data/eugene-silver-lake-stripped.html") as fh:
        content = fh.read().encode()
    return content

# Duplicated from `test_decode.py`
@pytest.fixture(scope="module")
def archival_data():
    with open("tests/data/SIRO1604-example.txt") as fh:
        data = fh.read()
    return data

# Duplicated from `test_compressed.py`
@pytest.fixture(scope="module")
def prepared_download_page():
    with open("tests/data/prepared-download-stripped.html") as fh:
        page = fh.read().encode()
    return page

# Duplicated from `test_compressed.py`
@pytest.fixture(scope="module")
def zipped_filenames():
    filenames = ("a.txt", "b.txt")
    return filenames

# Modified from `test_compressed.py`
@pytest.fixture(scope="module")
def zipped_data(zipped_filenames, archival_data):
    buffer = BytesIO()
    with ZipFile(buffer, mode="w") as zf:
        for filename in zipped_filenames:
            zf.writestr(filename, archival_data)

    yield buffer.getvalue()
    buffer.close()


@pytest.mark.usefixtures("clear_response_cache")
class TestFindFiles(object):
    @responses.activate
    def test_mocked(self, listing_content):
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
            body=listing_content
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
    def test_mocked(self, listing_content, prepared_download_page):
        expected_path = f"download/temp/33729216.zip"
        stations = ["Silver Lake"]
        start = end = date(2018, 1, 1)

        responses.add(
            responses.POST,
            f"{BASE_URL}/{LIST_FILES_PATH}",
            body=listing_content
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

@pytest.mark.usefixtures("clear_response_cache")
class TestFetchCompressed(object):
    @responses.activate
    def test_mocked(self, zipped_filenames, zipped_data):
        filepath = "download/temp/12345.zip"
        responses.add(responses.GET, f"{BASE_URL}/{filepath}", body=zipped_data)

        filestems, station_ids, contents = zip(*fetch_compressed(filepath))
        assert filestems == ("a", "b")
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
