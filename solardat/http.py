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

    def get_etag(self, path: str) -> Optional[str]:
        cached_response = self[path]
        if cached_response is None:
            return None
        return cached_response.headers["ETag"]

    def check_response(self, path: str, response: Response) -> Response:
        if response.status_code != 304:
            self._cache[path] = response
            return response
        cached_response = self._cache[path]
        if cached_response is None:
            raise RuntimeError
        return cached_response

_cache = _ResponseCache()

def dispatch(method: str, path: str, **kwds) -> Response:  # noqa: E501
    if method not in ("GET", "POST"):
        raise ValueError

    url = f"{BASE_URL}/{path}"
    etag = _cache.get_etag(path)

    kwds = kwds.copy()
    kwds["headers"] = {
        **kwds.get("headers", {}),
        "If-None-Match": etag,
    }

    response = requests.request(method, url, **kwds)
    response.raise_for_status()
    return _cache.check_response(path, response)
