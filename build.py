import os
import shutil
import sys

from scripts import transformer, reader, generator

# Create the out/ folder if it doesn't exist, by copying everything
# inside the template folder
shutil.copytree("template", "out")

# Create the entries folder, and copy the entire assets folder into it
os.mkdir("out/entries")
shutil.copytree("entries/assets", "out/entries/assets")

# Read and process the entries
include_drafts = "--drafts" in sys.argv
raw_entries = reader.read_entries(include_drafts)
entries = list(map(transformer.process_entry, raw_entries))

# Generate and write the index page
template = open("template/template.html", "r", encoding="utf-8").read()
index_content = generator.make_index(template, entries)

with open("out/index.html", "w", encoding="utf-8") as f:
    f.write(index_content)

# Generate the individual entries
for entry in entries:
    entry_content = generator.make_entry(template, entry)

    with open(f"out/entries/{entry.url}.html", "w", encoding="utf-8") as f:
        f.write(entry_content)

# Generate the RSS feed
rss = generator.make_rss(entries)
with open(f"out/rss.xml", "w", encoding="utf-8") as f:
    f.write(rss)

# Finally, remove the template from the out/ folder
os.remove("out/template.html")
