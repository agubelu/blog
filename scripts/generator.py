from typing import List
from scripts.types import ProcessedEntry
from feedgen.feed import FeedGenerator

def make_index(template: str, entries: List[ProcessedEntry]) -> str:
    # Title and preview, which are used for embedding metadata
    # are set to some generic string for the blog's index
    title = "blog.borrego.dev"
    preview = "Agustín Borrego's blog"

    # The link to go back to the index is unset
    back_home = ""

    # Main content block for all entries
    entry_content = ""
    for entry in entries:
        entry_content += f"""
            <div class="entry">
                <h1 class="entry-title">
                    <a href="entries/{entry.url}.html">{entry.title}</a>
                </h1>
                <span class="entry-date">{entry.date}</span>
                <p>{entry.preview}</p>
            </div>

            <hr>"""
        
    return template.format(
        title=title,
        preview=preview,
        back_home=back_home,
        entry_content=entry_content
    )

def make_entry(template: str, entry: ProcessedEntry) -> str:
    # Title and preview for embedding metadata, specific for this entry
    title = entry.title
    preview = entry.preview

    # Link to go back to the index
    back_home = '<a href="/"><i class="fa fa-arrow-left" aria-hidden="true"></i> Back to index</a>'

    # Main content block
    entry_content = f"""
            <div class="entry">
                <h1 class="entry-title">{entry.title}</h1>
                <span class="entry-date">{entry.date}</span>
                
                {entry.html_content}
            </div>

            <hr>"""
        
    return template.format(
        title=title,
        preview=preview,
        back_home=back_home,
        entry_content=entry_content
    )

def make_rss(entries: List[ProcessedEntry]) -> str:
    fg = FeedGenerator()

    fg.id("https://blog.borrego.dev")
    fg.title("blog.borrego.dev")
    fg.description("Agustín Borrego's blog")
    fg.author({"name":"Agustín Borrego","email":"agu@borrego.dev"})
    fg.link(href="https://blog.borrego.dev", rel="self")
    fg.language("en")

    for entry in entries:
        fe = fg.add_entry()
        fe.id(entry.url)
        fe.title(entry.title)
        fe.description(entry.preview)
        fe.link(href=f"https://blog.borrego.dev/entries/{entry.url}.html")
    
    return fg.rss_str(pretty=True).decode("utf-8")
