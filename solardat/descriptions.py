from collections import ChainMap
from pkgutil import get_data
from typing import Dict, ChainMap as TChainMap
import json


QC_FLAG_LENGTH = 2
OTHER_CODE_LENGTH = 3
SPECTRAL_CODE_LENGTH = 4
VALID_CODE_LENGTHS = (QC_FLAG_LENGTH, OTHER_CODE_LENGTH, SPECTRAL_CODE_LENGTH)


def _get_tables() -> Dict[str, Dict[str, str]]:
    contents = get_data("solardat", "resources/descriptions.json")
    if contents is None:
        raise RuntimeError("Package data not available")

    tables = json.loads(contents)
    for tablename, table in tables.items():
        for code, description in table.items():
            concise_description = "; ".join(description.split("\n"))
            tables[tablename][code] = concise_description
    return tables

def _merge_tables(tables: Dict[str, Dict[str, str]]) -> TChainMap[str, str]:
    return ChainMap(*[table for table in tables.values()])

tables = _get_tables()
tablenames = set(tables)
_merged_table = _merge_tables(tables)

def lookup_code(code: str) -> str:
    if len(code) not in VALID_CODE_LENGTHS:
        raise ValueError(f"The length of `code` must be one of {VALID_CODE_LENGTHS}")

    if len(code) == QC_FLAG_LENGTH:
        description = _merged_table[code]
    elif len(code) == OTHER_CODE_LENGTH:
        description = _merged_table[code]
    else:
        try:
            description = _merged_table[code]
        except KeyError:
            # The code could be a data element with an instrument
            # number (i.e. solar or meteorological). Drop it and
            # try again.
            try:
                description = _merged_table[code[:OTHER_CODE_LENGTH]]
            except KeyError:
                raise ValueError("Unknown code: {code}")

    return description
