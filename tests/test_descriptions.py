from unittest import mock
import pytest

from solardat.descriptions import _get_tables, _merge_tables, lookup_code


mock_table = {
    "10": "Quality",
    "100": "Solar",
    "1000": "Spectral",
}

@mock.patch("solardat.descriptions._merged_table", mock_table)
class TestLookupDescription(object):
    @pytest.mark.parametrize("code", ["1", "10000"], ids=["Short", "Long"])
    def test_validates_code_length(self, code):
        with pytest.raises(ValueError):
            lookup_code(code)

    @pytest.mark.parametrize("code, expected", [
        ("1000", "Spectral"),
        ("10", "Quality"),
        ("100", "Solar"),
        ("1002", "Solar"),
    ], ids=[
        "Spectral",
        "Quality Control",
        "Solar without instrument",
        "Solar with instrument"
    ])
    def test_lookup_code(self, code, expected):
        assert lookup_code(code) == expected

class TestTableMerging(object):
    def test_no_collisions(self):
        tables = _get_tables()
        merged_table = _merge_tables(tables)
        total_values = sum(len(values) for values in tables.values())
        assert len(merged_table) == total_values
