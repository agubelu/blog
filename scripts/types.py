from typing import NamedTuple

class RawEntry(NamedTuple):
    content: str
    filename: str

class ProcessedEntry(NamedTuple):
    url: str
    date: str
    title: str
    preview: str
    html_content: str