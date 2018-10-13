"""Decode archival data file.

See http://solardat.uoregon.edu/ArchivalFiles.html for a description.
"""

from collections import OrderedDict
from typing import Dict, Iterator, List, Tuple, Union
import csv


Num = Union[int, float]
Row = Dict[str, Num]
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

def cast_row(record: Dict[str, str]) -> Row:
    out: OrderedDict[str, Num] = OrderedDict()

    # Day of year and elapsed time since last measurement. The
    # latter has units (e.g. second/minute/hour) implicit to
    # the file.
    for column in FIRST_COLUMNS:
        out[column] = int(record[column])

    keys = list(record)[2:]
    for measure, flag in zip(keys[0::2], keys[1::2]):
        # Assume measurement will always be either an int or float.
        out[measure] = float(record[measure])
        out[flag] = int(record[flag])

    return out

def parse_archival(stream: Readable) -> Tuple[int, int, List[Row]]:
    header = next(stream)
    header_values = header.split(DELIMITER)
    station_id, year, columns = parse_header(header_values)

    reader = csv.DictReader(stream, fieldnames=columns, delimiter=DELIMITER)
    records = list(map(cast_row, reader))

    return station_id, year, records
