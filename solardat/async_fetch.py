"""Asynchronous versions of fetching data."""

from aiohttp import ClientResponse, ClientSession
from pathlib import Path
from requests.cookies import cookiejar_from_dict
from requests.models import Response
from requests.structures import CaseInsensitiveDict
from typing import Iterable, List, Tuple

from .decode import Row, read_raw
from .http import _cache, add_etag, make_url


# XXX: Creating a subclass of `Response` with restricted access would be
#      better.
async def wrap_async(response: ClientResponse) -> Response:
    """Build a ``requests`` response from a ``aiohttp`` response.

    A ``requests.Response`` instance is built to provide synchronous
    access to the original response's data. Note that the returned
    response does not have proper data for :attr:``elapsed`` or
    :attr:``request``.

    The response will be consumed if it has not already.
    """

    # Ensure the response data is read so that the wrapped response
    # does not require any async methods.
    await response.read()

    wrapped = Response()
    wrapped._content = response._body  # type: ignore
    wrapped._content_consumed = True  # type: ignore
    wrapped.status_code = response.status
    wrapped.headers = CaseInsensitiveDict(response.headers)
    wrapped.url = str(response.url)  # `aiohttp` uses a `URL` object.
    wrapped.encoding = response.get_encoding()
    wrapped.history = [await wrap_async(rsp) for rsp in response.history]
    wrapped.reason = response.reason or ""
    wrapped.cookies = cookiejar_from_dict(response.cookies)
    return wrapped

async def fetch_file(session: ClientSession, path: str, **kwds) -> Tuple[int, List[Row]]:
    """Get the contents of an archival data file asynchronously.

    Asynchronous version of :func:`~solardat.fetch.fetch_file`.

    Parameters
    ----------
    session : aiohttp.ClientSession
        The client session to use.
    path : str
        URL path component to the archival data file to
        be retrieved.
    **kwds
        Additional parameters to be used in the request.

    Returns
    -------
    station_id, rows : Tuple[int, List[OrderedDict]]
        The archival data, as well as the station's id.
    """

    headers = add_etag(path, kwds.get("headers", {}))
    if headers:
        kwds["headers"] = headers

    async with session.get(make_url(path), **kwds) as response:
        wrapped = await wrap_async(response)
        checked = _cache.check_response(path, wrapped)
        station_id, rows = read_raw(checked.text)
        return station_id, rows

_Ret = Tuple[str, int, List[Row]]

async def fetch_many(session: ClientSession, paths: Iterable[str], **kwds) -> List[_Ret]:
    """Get contents of multiple archival data files asynchronously.

    Parameters
    ----------
    session : aiohttp.ClientSession
        The client session to use.
    paths : Iterable[str]
        URL path components to the archival data files to
        be retrieved.
    **kwds
        Additional parameters to be used in each request.

    Returns
    -------
    List[Tuple[str, int, List[OrderedDict]]
        Archival data from each file, as well as the station id. The
        file's stem is returned for identification purposes.

    Examples
    --------
    >>> import aiohttp
    >>> import asyncio
    >>>
    >>> async def driver(paths):
    ...     async with aiohttp.ClientSession() as session:
    ...         results = await fetch_many(session, paths)
    ...         for filestem, station_id, rows in results:
    ...             print(filestem, station_id, len(rows))
    >>>
    >>> paths = [
    ...    "download/Archive/EUPH1801.txt",
    ...    "download/Archive/EUPH1802.txt",
    ... ]
    >>> loop = asyncio.get_event_loop()
    >>> loop.run_until_complete(driver(paths))
    EUPH1801 94255 744
    EUPH1802 94255 672
    """

    results = []
    for path in paths:
        filestem = Path(path).stem
        station_id, rows = await fetch_file(session, path, **kwds)
        results.append((filestem, station_id, rows))
    return results
