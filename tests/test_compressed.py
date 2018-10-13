from io import BytesIO
from zipfile import ZipFile
import pytest
import responses

from solardat.http import BASE_URL
from solardat.compressed import (
    is_zipfile_url,
    make_zipfile_form,
    prepare_zipfile,
    zipfile_link,
    zipped,
)


@pytest.fixture(scope="module")
def listing_page():
    with open("tests/data/eugene-silver-lake-stripped.html") as fh:
        page = fh.read().encode()
    return page

@pytest.fixture(scope="module")
def prepared_download_page():
    with open("tests/data/prepared-download-stripped.html") as fh:
        page = fh.read().encode()
    return page

@pytest.fixture(scope="module")
def zipped_data():
    filenames = ("a.txt", "b.txt")
    buffer = BytesIO()
    with ZipFile(buffer, mode="w") as zf:
        for filename in filenames:
            zf.writestr(filename, "TEST")

    yield buffer.getvalue()
    buffer.close()


class TestPrepareRequest(object):
    def test_make_zipfile_form(self, listing_page):
        expected = {
            "FileList": "51557993",
            "FileType": "ZIP",
            "Subdirectory": "Archive",
            "Submit": "Create+compressed+file",
        }

        form = make_zipfile_form(listing_page)
        assert form == expected

    @responses.activate
    def test_prepare_zipfile(self, prepared_download_page):
        responses.add(
            responses.POST,
            f"{BASE_URL}/cgi-bin/CompressDataFiles.cgi",
            body=prepared_download_page
        )

        page = prepare_zipfile(None)
        assert page == prepared_download_page

class TestDownload(object):
    @pytest.mark.parametrize("path, expected", [
        ("help/AdditionalInformation.html", False),
        ("download/temp/12345.zip", True),
    ])
    def test_is_zipfile_url(self, path, expected):
        assert is_zipfile_url(path) == expected

    def test_extracts_link(self, prepared_download_page):
        expected_url = f"{BASE_URL}/download/temp/33729216.zip"
        url = zipfile_link(prepared_download_page)
        assert url == expected_url

    @responses.activate
    def test_download(self, zipped_data):
        expected_len = 2
        expected_data = "TEST"

        path = "download/temp/12345.zip"
        responses.add(responses.GET, f"{BASE_URL}/{path}", body=zipped_data)

        extracted = list(zipped(path))
        assert len(extracted) == expected_len
        assert all(data == expected_data for data in extracted)
