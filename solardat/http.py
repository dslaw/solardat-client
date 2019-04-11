from requests.models import Response
from typing import Dict, Optional
import requests


BASE_URL = "http://solardat.uoregon.edu"


class _ResponseCache(object):
    """Cache for HTTP responses."""

    def __init__(self) -> None:
        self._cache: Dict[str, Optional[Response]] = {}

    def __getitem__(self, path: str) -> Optional[Response]:
        if path not in self._cache:
            self._cache[path] = None
        return self._cache[path]

    def __setitem__(self, path: str, value: Optional[Response]) -> None:
        self._cache[path] = value

    def clear(self) -> None:
        self._cache = {}

    def get_etag(self, path: str) -> Optional[str]:
        cached_response = self[path]
        if cached_response is None:
            return None
        return cached_response.headers.get("ETag")

    def check_response(self, path: str, response: Response) -> Response:
        response.raise_for_status()

        if response.status_code != 304:
            self[path] = response
            return response

        cached_response = self[path]
        if cached_response is None:
            # Should not occur if the cache is only mutated
            # through this method.
            raise RuntimeError
        return cached_response

_cache = _ResponseCache()

def add_etag(path: str, headers: Dict[str, str]) -> Dict[str, str]:
    etag = _cache.get_etag(path)
    if etag is None:
        return headers
    return {**headers, "If-None-Match": etag}

def make_url(path: str) -> str:
    return f"{BASE_URL}/{path}"

def dispatch(method: str, path: str, **kwds) -> requests.Response:
    if method not in ("GET", "POST"):
        raise ValueError

    headers = add_etag(path, kwds.get("headers", {}))
    if headers:
        kwds["headers"] = headers

    response = requests.request(method, make_url(path), **kwds)
    return _cache.check_response(path, response)
