from typing import List
from scripts.types import RawEntry

import os

def read_entries(include_drafts=False) -> List[RawEntry]:
    """
    Reads the entries from their folder and returns a list of pairs
    of their filename and raw content. The list is sorted with the
    newest entries first and oldest last.
    """

    raw_entries = _load_from("entries")
    if include_drafts:
        raw_entries += _load_from("drafts")

    raw_entries.sort(key=lambda e: e.filename, reverse=True)

    return raw_entries

def _load_from(folder) -> List[RawEntry]:
    files = [f for f in os.listdir(folder) if f.endswith(".md")]
    return [RawEntry(filename=f, content=open(folder + "/" + f, encoding="utf-8").read())
        for f in files]