import pytest

from solardat.http import _cache


@pytest.fixture
def clear_response_cache():
    yield
    _cache.clear()
