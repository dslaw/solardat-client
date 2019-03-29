from datetime import date
import pytest
import responses

from solardat.http import BASE_URL
from solardat.search import (
    ARCHIVAL_PATH,
    LIST_FILES_PATH,
    extract_rel_links,
    extract_stations,
    is_download_url,
    make_search_form,
    rel_links_page,
    stations_page,
)


@pytest.fixture(scope="module")
def select_content():
    with open("tests/data/select-archival-stripped.html") as fh:
        content = fh.read().encode()
    return content

@pytest.fixture(scope="module")
def listing_content():
    with open("tests/data/eugene-silver-lake-stripped.html") as fh:
        content = fh.read().encode()
    return content


@pytest.mark.usefixtures("clear_response_cache")
class TestStations(object):
    @responses.activate
    def test_request(self, select_content):
        responses.add(
            responses.GET,
            f"{BASE_URL}/{ARCHIVAL_PATH}",
            body=select_content
        )
        content = stations_page()
        assert content == select_content

    def test_extracts(self, select_content):
        # NB: One is subtracted as "Richland" is displayed,
        #     but not selectable.
        expected_len = 7 + 1 + 28 + 1 + 4 + 1 - 1

        stations = extract_stations(select_content)
        assert len(stations) == expected_len
        # One example.
        assert "Eugene" in stations

    def test_external(self):
        expected_len = 7 + 1 + 28 + 1 + 4 + 1 - 1

        content = stations_page()
        stations = extract_stations(content)
        assert len(stations) == expected_len
        # One example.
        assert "Eugene" in stations

class TestIsDownloadURL(object):
    @pytest.mark.parametrize("path, expected", [
        ("help/AdditionalInformation.html", False),
        ("download/Archive/SIRO1401.txt", True),
    ], ids=["false", "true"])
    def test_matches(self, path, expected):
        assert is_download_url(path) == expected

@pytest.mark.usefixtures("clear_response_cache")
class TestArchivalSearch(object):
    stations = ("Eugene", "Silver Lake")
    start = date(2016, 1, 1)
    end = date(2016, 10, 1)

    def test_make_search_form(self):
        expected = {
            "CalledFrom": "MONTH_BLOCK",
            "StartMonth": "01",
            "StartYear": "2016",
            "EndMonth": "10",
            "EndYear": "2016",
            "SubmitButton": "Select files",
            "Eugene": "on",
            "Silver Lake": "on",
        }

        form = make_search_form(self.start, self.end, self.stations)
        assert form == expected

    @responses.activate
    def test_request(self, listing_content):
        responses.add(
            responses.POST,
            f"{BASE_URL}/{LIST_FILES_PATH}",
            body=listing_content
        )

        content = rel_links_page(self.start, self.end, self.stations)
        assert content == listing_content

    def test_extracts(self, listing_content):
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

        links = extract_rel_links(listing_content)
        assert links == expected

    def test_extracts_raises_if_no_table(self):
        content = b"<html><body><p>Hi</p></body></html>"
        with pytest.raises(RuntimeError):
            extract_rel_links(content)

    def test_external(self):
        expected_len = 2
        expected_counts = {"Eugene, OR": 40, "Silver Lake, OR": 20}

        content = rel_links_page(self.start, self.end, self.stations)
        links = extract_rel_links(content)
        link_counts = {key: len(value) for key, value in links.items()}

        assert len(links) == expected_len
        assert link_counts == expected_counts
