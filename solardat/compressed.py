from io import BytesIO
from lxml import html
from typing import Dict, Generator
from zipfile import ZipFile
import re

from .http import dispatch


def make_zipfile_form(page: bytes) -> Dict[str, str]:
    tree = html.fromstring(page)

    filelist_xpath = '//form[@method="POST"]/input[@name="FileList"]'
    subdirectory_xpath = '//form[@method="POST"]/input[@name="Subdirectory"]'
    filelist = tree.xpath(filelist_xpath)[0].value
    subdirectory = tree.xpath(subdirectory_xpath)[0].value

    return {
        "FileList": filelist,
        "FileType": "ZIP",
        "Subdirectory": subdirectory,
        "Submit": "Create+compressed+file",
    }

def prepare_zipfile(form: Dict[str, str]) -> bytes:
    path = "cgi-bin/CompressDataFiles.cgi"
    response = dispatch("POST", path, data=form)
    return response.content

def is_zipfile_url(path: str) -> bool:
    pattern = r"download/temp/\d+?\.zip"
    match = re.search(pattern, path)
    return match is not None

def zipfile_link(page: bytes) -> str:
    tree = html.fromstring(page)
    for _, _, ref, _ in tree.iterlinks():
        if is_zipfile_url(ref):
            return ref
    else:
        raise ValueError("Page did not contain a zipfile link")

# XXX: These files aren't associated with stations. To do so,
#      you'd have to get the association from the search results
#      page, invert station to filenames mapping and look up
#      the station from the filename in the zipfile.
def zipped(path: str) -> Generator[str, None, None]:
    response = dispatch("GET", path)

    with BytesIO(response.content) as buffer:
        with ZipFile(buffer) as zf:
            for filename in zf.namelist():
                data = zf.read(filename).decode()
                yield data
