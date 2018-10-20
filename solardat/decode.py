"""Decode archival data file.

See http://solardat.uoregon.edu/ArchivalFiles.html for a description.
"""

from collections import OrderedDict
from datetime import datetime
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

def cast_row(record: Dict[str, str], year: int) -> Row:
    out: OrderedDict[str, RowValue] = OrderedDict()

    # Include date information with the interval end time.
    doy = record["doy"]
    timestamp = int(record["ending_time"])
    hours, minutes = parse_timestamp(timestamp)
    out["ending_time"] = (
        datetime
        .strptime(f"{year}-{doy}", "%Y-%j")
        .replace(hour=hours, minute=minutes)
    )

    keys = list(record)[2:]
    for measure, flag in zip(keys[0::2], keys[1::2]):
        # Assume measurement will always be either an int or float.
        out[measure] = float(record[measure])
        out[flag] = int(record[flag])

    return out

def parse_archival(stream: Readable) -> Tuple[int, List[Row]]:
    header = next(stream)
    header_values = header.split(DELIMITER)
    station_id, year, columns = parse_header(header_values)

    reader = csv.DictReader(stream, fieldnames=columns, delimiter=DELIMITER)
    records = map(lambda record: cast_row(record, year), reader)

    return station_id, list(records)
