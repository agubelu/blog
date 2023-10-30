from typing import List
from scripts.types import RawEntry

import os

def read_entries() -> List[RawEntry]:
    """
    Reads the entries from their folder and returns a list of pairs
    of their filename and raw content. The list is sorted with the
    newest entries first and oldest last.
    """

    files = [f for f in os.listdir("entries") if f.endswith(".md")]
    raw_entries = [
        RawEntry(filename=f, content=open("entries/" + f).read())
        for f in files
    ]

    raw_entries.sort(key=lambda e: e.filename, reverse=True)

    return raw_entries