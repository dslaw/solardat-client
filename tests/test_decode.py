from collections import OrderedDict
from datetime import datetime
from io import StringIO
import pytest

from solardat.decode import (
    add_hours_minutes,
    cast_row,
    parse_archival,
    parse_header,
    parse_timestamp,
)


@pytest.fixture
def header_values():
    return [
        "94249", "2016",
        "1001", "0",
        "2011", "0",
        "3001", "0",
    ]

@pytest.fixture(scope="module")
def archival_data():
    with open("tests/data/SIRO1604-example.txt") as fh:
        data = fh.read()
    return data

@pytest.fixture
def buffer(archival_data):
    with StringIO(archival_data) as data_buffer:
        yield data_buffer


class TestParseHeader(object):
    def test_metadata(self, header_values):
        expected_station_id = 94249
        expected_year = 2016

        station_id, year, _ = parse_header(header_values)
        assert station_id == expected_station_id
        assert year == expected_year

    def test_columns(self, header_values):
        expected_columns = [
            "doy", "ending_time",
            "1001", "1001_FLAG",
            "2011", "2011_FLAG",
            "3001", "3001_FLAG",
        ]

        _, _, columns = parse_header(header_values)
        assert columns == expected_columns

class TestParseTimestamp(object):
    @pytest.mark.parametrize("timestamp, hours, minutes", [
        (200, 2, 0),
        (1500, 15, 0),
        (459, 4, 59),
        (1859, 18, 59),
        (130, 1, 30),
        (1030, 10, 30),
        (15, 0, 15),
    ], ids=[
        "Start of hour, single digit hour",
        "Start of hour, double digit hour",
        "End of hour, single digit hour",
        "End of hour, double digit hour",
        "Middle of hour, single digit hour",
        "Middle of hour, double digit hour",
        "Middle of hour, no hour digit",
    ])
    def test_parses(self, timestamp, hours, minutes):
        expected = (hours, minutes)
        assert parse_timestamp(timestamp) == expected

class TestAddHoursMinutes(object):
    def test_adjusts_for_midnight(self):
        ending = datetime(2000, 1, 1)
        expected = datetime(2000, 1, 2, 0, 0)

        out = add_hours_minutes(ending, hours=24, minutes=0)
        assert out == expected

    @pytest.mark.parametrize("hours, minutes, expected", [
        (5, 0, datetime(2000, 1, 1, 5, 0)),
        (0, 1, datetime(2000, 1, 1, 0, 1)),
        (5, 1, datetime(2000, 1, 1, 5, 1)),
    ], ids=["hours", "minutes", "hours and minutes"])
    def test_adds_time(self, hours, minutes, expected):
        ending = datetime(2000, 1, 1)
        out = add_hours_minutes(ending, hours, minutes)
        assert out == expected

class TestCastRow(object):
    def test_casts_values(self):
        year = 2010
        record = OrderedDict([
            ("doy", "10"),
            ("ending_time", "50"),
            ("1001", "1.23"),
            ("1001_FLAG", "9"),
            ("3001", "1"),
            ("3001_FLAG", "0"),
        ])
        expected = OrderedDict([
            ("ending_time", datetime(year, 1, 10, 0, 50)),
            ("1001", 1.23),
            ("1001_FLAG", 9),
            ("3001", 1.),
            ("3001_FLAG", 0),
        ])

        out = cast_row(record, year)
        assert out == expected

class TestParseArchival(object):
    def test_metadata(self, buffer):
        expected_station_id = 94249

        station_id, _ = parse_archival(buffer)

        assert station_id == expected_station_id

    def test_records(self, buffer):
        expected_len = 100
        expected_columns = {
            "ending_time",
            "1001", "1001_FLAG",
            "2011", "2011_FLAG",
            "3001", "3001_FLAG",
            "1961", "1961_FLAG",
            "9301", "9301_FLAG",
        }

        _, records = parse_archival(buffer)
        assert len(records) == expected_len
        assert all(set(record) == expected_columns for record in records)

    def test_file(self):
        with open("tests/data/SIRO1604-example.txt") as fh:
            out = parse_archival(fh)

        assert out
