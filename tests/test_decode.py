from collections import OrderedDict
from io import StringIO
import pytest

from solardat.decode import cast_row, parse_header, parse_archival


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

class TestCastRow(object):
    def test_casts_values(self):
        record = OrderedDict([
            ("doy", "10"),
            ("ending_time", "60"),
            ("1001", "1.23"),
            ("1001_FLAG", "9"),
            ("3001", "1"),
            ("3001_FLAG", "0"),
        ])
        expected = OrderedDict([
            ("doy", 10),
            ("ending_time", 60),
            ("1001", 1.23),
            ("1001_FLAG", 9),
            ("3001", 1.),
            ("3001_FLAG", 0),
        ])

        out = cast_row(record)
        assert out == expected

class TestParseArchival(object):
    def test_metadata(self, buffer):
        expected_station_id = 94249
        expected_year = 2016

        station_id, year, _ = parse_archival(buffer)

        assert station_id == expected_station_id
        assert year == expected_year

    def test_records(self, buffer):
        expected_len = 100
        expected_columns = {
            "doy", "ending_time",
            "1001", "1001_FLAG",
            "2011", "2011_FLAG",
            "3001", "3001_FLAG",
            "1961", "1961_FLAG",
            "9301", "9301_FLAG",
        }

        _, _, records = parse_archival(buffer)
        assert len(records) == expected_len
        assert all(set(record) == expected_columns for record in records)

    def test_file(self):
        with open("tests/data/SIRO1604-example.txt") as fh:
            out = parse_archival(fh)

        assert out
