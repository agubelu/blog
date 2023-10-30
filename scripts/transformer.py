import markdown
import re
from scripts.types import RawEntry, ProcessedEntry

RE_P = re.compile("<p>(.*?)</p>", re.DOTALL)

def process_entry(entry: RawEntry) -> ProcessedEntry:
    # Get the date and the URL from the filename
    date_raw, filename = entry.filename.split("_", maxsplit=1)
    url = filename.split(".")[0]

    # Get the title and the rest of the raw content
    title, content_raw = entry.content.split("---", maxsplit=1)

    # Transform the content into HTML
    html_content = markdown.markdown(content_raw.strip())

    # Extract the preview, which is the content of the first <p>
    # in the processed HTML
    preview = ""
    match = RE_P.search(html_content)
    if match:
        preview = match.group(1)
        if preview.endswith("."):
            preview += ".."
        else:
            preview += "..."

    return ProcessedEntry(url=url,
                          date=_transform_date(date_raw),
                          title=title.strip(),
                          preview=preview.strip(),
                          html_content=html_content)

def _transform_date(date: str) -> str:
    year, month, day = date.split("-")
    month_str = ["jan", "feb", "mar", "apr", "may", "jun", 
                 "jul", "aug", "sep", "oct", "nov", "dec"]
    return f"{day}/{month_str[int(month) - 1]}/{year}"
