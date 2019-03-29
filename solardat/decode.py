"""Decode archival data file.

See http://solardat.uoregon.edu/ArchivalFiles.html for a description.
"""

from collections import OrderedDict
from datetime import datetime, timedelta
from io import StringIO
from typing import Dict, Iterator, List, Tuple, Union
import csv


RowValue = Union[int, float, datetime]
Row = Dict[str, RowValue]
Readable = Iterator[str]


DELIMITER = "\t"
FIRST_COLUMNS = ("doy", "ending_time")


def parse_header(values: List[str]) -> Tuple[int, int, List[str]]:
    station_id, year, *descriptors = values

    columns = list(FIRST_COLUMNS)
    for element_no, flag in zip(descriptors[0::2], descriptors[1::2]):
        columns.append(element_no)
        columns.append(f"{element_no}_FLAG")

    return int(station_id), int(year), columns

def parse_timestamp(timestamp: int) -> Tuple[int, int]:
    hours, minutes = divmod(timestamp, 100)
    return hours, minutes

def add_hours_minutes(ending: datetime, hours: int, minutes: int) -> datetime:
    # 24:00 indicates that the interval ends on midnight of the next day.
    if hours == 24:
        ending = ending + timedelta(days=1)
        hours = 0
    return ending.replace(hour=hours, minute=minutes)

def cast_row(record: Dict[str, str], year: int) -> Row:
    out: OrderedDict[str, RowValue] = OrderedDict()

    # Include date information with the interval end time.
    doy = record["doy"]
    timestamp = int(record["ending_time"])
    hours, minutes = parse_timestamp(timestamp)
    ending_date = datetime.strptime(f"{year}-{doy}", "%Y-%j")
    out["ending_time"] = add_hours_minutes(ending_date, hours, minutes)

    keys = list(record)[2:]
    for measure, flag in zip(keys[0::2], keys[1::2]):
        # Assume measurement will always be either an int or float.
        out[measure] = float(record[measure])
        out[flag] = int(record[flag])

    return out

def parse_archival(handle: Readable) -> Tuple[int, List[Row]]:
    """Parse archival file data from a file-like object.

    For the format of the returned data, see :func:`~solardat.decode.read_raw`.

    Parameters
    ----------
    handle : Iterator[str]
        A file-like object used to iterate over the archival file
        data.

    Returns
    -------
    station_id, rows : Tuple[int, List[OrderedDict]]
        The archival data, as well as the station's id.

    Examples
    --------
    >>> with open("EUPQ1801.txt", "r") as fh:
    >>>     station_id, rows = parse_archival(fh)
    """

    header = next(handle)
    header_values = header.split(DELIMITER)
    station_id, year, columns = parse_header(header_values)

    reader = csv.DictReader(handle, fieldnames=columns, delimiter=DELIMITER)
    records = map(lambda record: cast_row(record, year), reader)

    return station_id, list(records)

def read_raw(contents: str) -> Tuple[int, List[Row]]:
    """Marshal the contents of an archival data file.

    The returned data uses the data element numbers as field
    names, where appropriate. Quality control flag field names
    are data element numbers with "_FLAG" appended, where the
    data element number indicates the measurement field that the
    flag corresponds to.

    Parameters
    ----------
    contents: str
        Archival data file contents as tab separated values.

    Returns
    -------
    station_id, rows : Tuple[int, List[OrderedDict]]
        The archival data, as well as the station's id.

    Examples
    --------
    >>> url = "http://solardat.uoregon.edu/download/Archive/EUPQ1801.txt"
    >>> response = requests.get(url)
    >>> station_id, rows = read_raw(response.text)
    """

    with StringIO(contents) as buffer:
        station_id, rows = parse_archival(buffer)
    return station_id, rows
