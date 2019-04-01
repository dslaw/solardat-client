import pytest

from solardat.http import _cache


@pytest.fixture
def clear_response_cache():
    yield
    _cache.clear()

@pytest.fixture(scope="module")
def search_results_page():
    with open("tests/data/eugene-silver-lake-stripped.html") as fh:
        content = fh.read().encode()
    return content

@pytest.fixture(scope="module")
def archival_data():
    with open("tests/data/SIRO1604-example.txt") as fh:
        data = fh.read()
    return data

@pytest.fixture(scope="module")
def prepared_download_page():
    with open("tests/data/prepared-download-stripped.html") as fh:
        page = fh.read().encode()
    return page
