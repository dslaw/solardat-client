from requests.exceptions import HTTPError
from requests.models import Response
import pytest
import responses

from solardat.http import _ResponseCache, _cache, BASE_URL, dispatch


def populated_cache():
    cache = _ResponseCache()
    response = Response()
    response.headers = {"ETag": "etag"}
    cache._cache["path/resource"] = response
    return cache, response

@pytest.fixture
def setup_cache():
    response = Response()
    response.headers = {"ETag": "etag"}
    response.status_code = 200
    _cache["test"] = response
    yield
    del _cache._cache["test"]


class TestResponseCache(object):
    path = "path/resource"

    def test_getitem_present(self):
        cache, response = populated_cache()

        out = cache[self.path]
        assert out is response

    def test_getitem_missing(self):
        cache = _ResponseCache()

        out = cache[self.path]
        assert out is None
        # Attempted access adds as null.
        assert cache._cache[self.path] is None

    def test_setitem(self):
        response = Response()
        cache = _ResponseCache()

        cache[self.path] = response
        assert cache._cache.get(self.path) is response

    def test_get_etag_present(self):
        cache, response = populated_cache()

        out = cache.get_etag(self.path)
        assert out == "etag"

    def test_get_etag_missing(self):
        cache = _ResponseCache()

        out = cache.get_etag(self.path)
        assert out is None

    def test_get_etag_missing_header(self):
        cache = _ResponseCache()
        response = Response()
        response.headers = {}
        cache[self.path] = response

        out = cache.get_etag(self.path)
        assert out is None

    def test_clear_cache(self):
        cache, _ = populated_cache()

        cache.clear()
        assert not cache._cache

def callback(request):
    # `requests` strips out headers with null keys.
    etag = request.headers.get("If-None-Match")
    if etag == "etag":
        return (304, {}, "")

    headers = {"ETag": "etag"}
    return (200, headers, "")

class TestDispatch(object):
    path = "test"

    @pytest.mark.parametrize("method", ["DELETE", "HEAD", "OPTIONS", "PATCH", "PUT"])
    @responses.activate  # Make sure there's no outbound traffic.
    def test_validates_method(self, method):
        with pytest.raises(ValueError):
            dispatch(method, self.path)

    @responses.activate
    def test_from_cache(self, setup_cache):
        responses.add_callback(responses.GET, f"{BASE_URL}/test", callback=callback)
        response = dispatch("GET", self.path)
        assert response is _cache[self.path]

    @responses.activate
    def test_request(self):
        responses.add_callback(responses.GET, f"{BASE_URL}/test", callback=callback)
        response = dispatch("GET", self.path)
        assert response is _cache[self.path]

    @responses.activate
    def test_raises(self):
        responses.add(responses.GET, f"{BASE_URL}/non-existent", status=400)
        with pytest.raises(HTTPError):
            dispatch("GET", "non-existent")
