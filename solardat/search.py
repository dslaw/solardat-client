from collections import defaultdict
from datetime import date
from lxml import html
from typing import DefaultDict, Dict, List
import re

from .http import dispatch


ARCHIVAL_PATH = "SelectArchival.html"
LIST_FILES_PATH = "cgi-bin/ShowArchivalFiles.cgi"


def stations_page() -> bytes:
    response = dispatch("GET", ARCHIVAL_PATH)
    return response.content

def extract_stations(page: bytes) -> List[str]:
    xpath = '//table/tr/td/input[@type="CHECKBOX"]/following::td[1]'
    tree = html.fromstring(page)
    return [ele.text for ele in tree.xpath(xpath)]

def make_search_form(start: date, end: date, stations: List[str]) -> Dict[str, str]:
    selected_stations = {station: "on" for station in stations}
    return {
        "CalledFrom": "MONTH_BLOCK",
        "StartMonth": str(start.month).zfill(2),
        "StartYear": str(start.year),
        "EndMonth": str(end.month).zfill(2),
        "EndYear": str(end.year),
        "SubmitButton": "Select files",
        **selected_stations,
    }

def is_download_url(url: str) -> bool:
    pattern = r"download/Archive/\w+?\.txt"
    match = re.search(pattern, url)
    return match is not None

def rel_links_page(start: date, end: date, stations: List[str]) -> bytes:
    form = make_search_form(start, end, stations)
    response = dispatch("POST", LIST_FILES_PATH, data=form)
    return response.content

def extract_rel_links(page: bytes) -> Dict[str, List[str]]:
    tree = html.fromstring(page)

    # Find the table with the actual search results in it.
    table_xpath = (
        '//table[@border="1" and '
        '@cellspacing="0" and '
        '@cellpadding="2"]'
    )
    tables = tree.xpath(table_xpath)
    if not tables:
        raise RuntimeError("Unable to find links")

    table = tables[0]
    table_body = table[0]

    # Stations are "delimited" by having a full table width row
    # with the station name in it. All rows after are associated
    # with that station, until another full width row appears or
    # the footer row appears.
    subheading_xpath = 'td[@align="CENTER" and @colspan="3"]'
    all_links: DefaultDict[str, List[str]] = defaultdict(list)
    station = None
    for row in table_body:
        # Check that the row contains the station subheader.
        subheadings = row.xpath(subheading_xpath)
        if subheadings:
            subheading = subheadings[0]
            wrapper = subheading[0]
            station = wrapper.text
            continue

        if station is None:
            continue

        for _, _, link, _ in row.iterlinks():
            # TODO: check assumption that one row = one link
            if is_download_url(link):
                all_links[station].append(link)

    return dict(all_links)
