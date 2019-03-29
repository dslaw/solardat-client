from datetime import date
from urllib.parse import urlparse
from io import BytesIO
from pathlib import Path
from typing import Dict, Iterator, List, Tuple
from zipfile import ZipFile

from .compressed import make_zipfile_form, prepare_zipfile, zipfile_link
from .decode import Row, read_raw
from .http import dispatch
from .search import extract_rel_links, rel_links_page


def find_files(start: date, end: date, stations: List[str]) -> Dict[str, List[str]]:
    """Search for archival data files.

    Parameters
    ----------
    start: date
        Start of the search interval. Only the month and year
        are used.
    end: date
        End of the search interval, inclusive. Only the month
        and year are used.
    stations: List[str]
        Stations to be included in the search results.

    Returns
    -------
    paths : Dict[str, List[str]]
        URL path components to the data files matching the query,
        organized by station. The returned station name may not
        match the input station name.

    Examples
    --------
    >>> stations = ["Eugene"]
    >>> start = date(2018, 1, 1)
    >>> end = date(2018, 2, 1)
    >>> paths = find_files(start, end, stations)
    {'Eugene, OR': ['download/Archive/EUPF1801.txt',
      'download/Archive/EUPF1802.txt',
      'download/Archive/EUPH1801.txt',
      'download/Archive/EUPH1802.txt',
      'download/Archive/EUPO1801.txt',
      'download/Archive/EUPO1802.txt',
      'download/Archive/EUPQ1801.txt',
      'download/Archive/EUPQ1802.txt']}
    """
    page = rel_links_page(start, end, stations)
    return extract_rel_links(page)

def fetch_file(path: str) -> Tuple[int, List[Row]]:
    """Get the contents of an archival data file.

    For the format of the returned data, see :func:`~solardat.decode.read_raw`.

    Parameters
    ----------
    path : str
        URL path component to the archival data file to
        be retrieved.

    Returns
    -------
    station_id, rows : Tuple[int, List[OrderedDict]]
        The archival data, as well as the station's id.

    Examples
    --------
    >>> path = "download/Archive/EUPQ1801.txt"
    >>> station_id, rows = fetch_file(path)
    >>> station_id
    94255
    >>> rows[0]
    OrderedDict([('ending_time', datetime.datetime(2018, 1, 1, 0, 15)),
                 ('1000', 0.0),
                 ('1000_FLAG', 12),
                 ('2010', 0.0),
                 ('2010_FLAG', 12),
                 ('2011_FLAG', 0.0),
                 ('2011_FLAG', 12),
                 ...
                 ])
    """

    response = dispatch("GET", path)
    station_id, rows = read_raw(response.text)
    return station_id, rows

def find_compressed(start: date, end: date, stations: List[str]) -> str:
    """Search for archival data files and return the zipfile path.

    Get the path to download a temporary zipfile containing the
    archival data files returned by the query.

    Parameters
    ----------
    start: date
        Start of the search interval. Only the month and year
        are used.
    end: date
        End of the search interval, inclusive. Only the month
        and year are used.
    stations: List[str]
        Stations to be included in the search results.

    Returns
    -------
    path : str
        URL path component to the zipfile.

    Examples
    --------
    >>> stations = ["Eugene"]
    >>> start = date(2018, 1, 1)
    >>> end = date(2018, 2, 1)
    >>> zipfile_path = find_compressed(start, end, stations)
    >>> zipfile_path
    'download/temp/67350228.zip'
    """

    # Search.
    page = rel_links_page(start, end, stations)

    # Ask the server to zip the search results.
    zipfile_form = make_zipfile_form(page)
    download_page = prepare_zipfile(zipfile_form)

    # Get link to the temporary zipfile.
    url = zipfile_link(download_page)
    parsed = urlparse(url)
    return parsed.path.lstrip("/")

def fetch_compressed(path: str) -> Iterator[Tuple[str, int, List[Row]]]:
    """Get the contents of compressed archival data files.

    The entire zipfile is brought into memory and the contents of
    each archival data file returned.

    For the format of the returned data, see :func:`~solardat.decode.read_raw`.

    Parameters
    ----------
    path : str
        URL path component to the archival data file to
        be retrieved.

    Returns
    -------
    Iterator[Tuple[str, int, List[Row]]]
        Generator over the archival data files contained in the
        compressed file. Each item corresponds to a single archival
        data file, with the filestem, station id and archival data.

    Examples
    --------
    >>> start = date(2018, 1, 1)
    >>> end = date(2018, 1, 1)
    >>> stations = ["Eugene"]
    >>> zipfile_path = find_compressed(start, end, stations)
    >>> for filestem, station_id, rows in fetch_compressed(zipfile_path):
    >>>     print(filestem, station_id, len(rows))
    EUPF1801 94255 8928
    EUPH1801 94255 744
    EUPO1801 94255 44640
    EUPQ1801 94255 2976
    """

    response = dispatch("GET", path)
    with BytesIO(response.content) as buffer:
        with ZipFile(buffer) as zf:
            for filename in zf.namelist():
                file = Path(filename)
                file_contents = zf.read(filename).decode()
                station_id, rows = read_raw(file_contents)
                yield file.stem, station_id, rows
