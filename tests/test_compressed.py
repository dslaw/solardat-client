import pytest
import responses

from solardat.http import BASE_URL
from solardat.compressed import (
    is_zipfile_url,
    make_zipfile_form,
    prepare_zipfile,
    zipfile_link,
)


@pytest.mark.usefixtures("clear_response_cache")
class TestPrepareRequest(object):
    def test_make_zipfile_form(self, search_results_page):
        expected = {
            "FileList": "51557993",
            "FileType": "ZIP",
            "Subdirectory": "Archive",
            "Submit": "Create+compressed+file",
        }

        form = make_zipfile_form(search_results_page)
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

@pytest.mark.usefixtures("clear_response_cache")
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
