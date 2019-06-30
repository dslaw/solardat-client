"""Get and print codes.

Read the tables for data element numbers and quality control flags
from the website and generate machine readable versions of them.
The codes and corresponding descriptions from each table are printed
as a single JSON object, where codes and descriptoins are both represented as
strings. The latter with newlines separating each level in the hierarchy.
"""
# XXX: Second spectral digit is broken - both values are 0!

from lxml import html
from typing import Dict, List, NamedTuple, Optional
import json
import requests


DELIMITER = "\x97"  # &#151;
MIN_COLSPAN = 1
DATA_ELEMENT_URL = "http://solardat.uoregon.edu/DataElementNumbers.html"
QUALITY_CONTROL_URL = "http://solardat.uoregon.edu/QualityControlFlags.html"
TABLE_XPATH = '//table[@cellpadding="4" and @cellspacing="0" and @border="1"]'


DescriptionTable = Dict[str, str]

class _Node(NamedTuple):
    digit: str
    description: str


def make_node(ele: html.HtmlElement) -> _Node:
    digit, description = map(str.strip, ele.text.split(DELIMITER))

    # Check if `lxml` skipped over the textual content because
    # it's within a link. And assume that the entirety of missing
    # text is the link.
    if not description:
        link_ele = ele.find("a")
        if link_ele is not None:
            description = link_ele.text

    description = " ".join(description.split())
    return _Node(digit, description)

def get_max_colspan(table: html.HtmlElement) -> int:
    elements = [row[-1] for row in table]
    colspans = [ele.get("colspan", MIN_COLSPAN) for ele in elements]
    return max(map(int, colspans))

def parse_table(table: html.HtmlElement) -> DescriptionTable:
    max_colspan = get_max_colspan(table)

    codes: DescriptionTable = {}
    current: List[Optional[_Node]] = [None] * max_colspan
    for row in table:
        # There will be either one or two cells. If two, the first
        # is just padding. So we always want the last one in the row.
        ele = row[-1]

        # The row may not have an element number description.
        if DELIMITER not in ele.text:
            continue

        node = make_node(ele)
        colspan = int(ele.get("colspan", MIN_COLSPAN))
        depth = max_colspan - colspan

        current[depth] = node

        if colspan == MIN_COLSPAN:
            nodes = [node for node in current if node is not None]
            code = "".join(node.digit for node in nodes)
            descriptions = "\n".join(node.description for node in nodes)
            codes.update({code: descriptions})
            current[depth] = None

    return codes

def get_tables(url: str) -> List[DescriptionTable]:
    response = requests.get(url)
    response.raise_for_status()
    tree = html.fromstring(response.content)
    tables = map(parse_table, tree.xpath(TABLE_XPATH))
    return list(tables)

def data_element_tables() -> Dict[str, DescriptionTable]:
    names = ("solar", "spectral", "meteorological")
    tables = get_tables(DATA_ELEMENT_URL)
    return {name: table for name, table in zip(names, tables)}

def quality_control_table() -> DescriptionTable:
    table, *_ = get_tables(QUALITY_CONTROL_URL)
    return table


if __name__ == "__main__":
    all_tables = {
        **data_element_tables(),
        "quality": quality_control_table(),
    }
    print(json.dumps(all_tables, indent=2))
