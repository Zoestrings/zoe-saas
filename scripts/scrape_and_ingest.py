"""Scrape website content, extract clean text, and ingest into Zoe knowledge base."""

import argparse
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import requests

from zoe.knowledge.ingestion import ingest_document
from zoe.knowledge.retriever import search
from zoe.utils.logging import get_logger

logger = get_logger("zoe.scripts.scrape_and_ingest")


def clean_html_content(html: str) -> str:
    """Parse HTML and extract meaningful text content while stripping boilerplate."""
    soup = BeautifulSoup(html, "html.parser")

    # 1. Remove non-content elements
    for element in soup(["script", "style", "noscript", "header", "footer", "nav", "aside", "svg", "form", "iframe"]):
        element.extract()

    # 2. Extract title & meta description if available
    lines = []
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
        if title:
            lines.append(f"Title: {title}")

    meta_desc = soup.find("meta", attrs={"name": re.compile(r"description", re.IGNORECASE)})
    if meta_desc and meta_desc.get("content"):
        desc = meta_desc["content"].strip()
        if desc:
            lines.append(f"Description: {desc}")

    # 3. Extract text from structural text tags in document order
    body = soup.find("body") or soup
    text_chunks = []
    for tag in body.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "article", "section"]):
        txt = tag.get_text(separator=" ", strip=True)
        if txt and len(txt) > 10:
            text_chunks.append(txt)

    # Fallback to general get_text if specific tags are sparse
    if len(text_chunks) < 3:
        raw_text = body.get_text(separator="\n", strip=True)
        clean_lines = [l.strip() for l in raw_text.splitlines() if l.strip() and len(l.strip()) > 3]
        text_chunks = clean_lines

    # Deduplicate adjacent identical chunks while preserving order
    deduped = []
    for c in text_chunks:
        if not deduped or deduped[-1] != c:
            deduped.append(c)

    content_body = "\n\n".join(deduped)
    if lines:
        return "\n".join(lines) + "\n\n" + content_body
    return content_body


def derive_domain_filename(url: str) -> str:
    """Extract clean domain name from URL for the filename."""
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    if not netloc:
        netloc = parsed.path.lower().split("/")[0]

    # Remove standard prefixes like www.
    clean_domain = re.sub(r"^www\.", "", netloc)
    # Remove port if present
    clean_domain = clean_domain.split(":")[0]
    # Replace non-alphanumeric with underscores
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", clean_domain).strip("_")
    return f"{slug}_info.txt"


def scrape_url(url: str, timeout: int = 15) -> str:
    """Fetch URL with browser-like headers and extract clean text."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    logger.info("Fetching URL: %s", url)
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()

    # Detect encoding if not explicitly set
    if response.encoding is None:
        response.encoding = "utf-8"

    return clean_html_content(response.text)


def main():
    parser = argparse.ArgumentParser(
        description="Scrape a website and ingest into Zoe official knowledge base."
    )
    parser.add_argument("url", nargs="?", help="URL of the website to scrape")
    parser.add_argument("--url", dest="url_opt", help="Alternative URL option flag")
    parser.add_argument("--project", default="live_test", help="Project ID (default: live_test)")
    parser.add_argument("--output-dir", default="data/knowledge", help="Directory to save scraped text")
    parser.add_argument("--filename", help="Custom output filename (optional)")
    args = parser.parse_args()

    target_url = args.url or args.url_opt
    if not target_url:
        parser.error("A URL must be provided as an argument or via --url.")

    if not target_url.startswith(("http://", "https://")):
        target_url = "https://" + target_url

    print("=" * 60)
    print(f"1. Scraping website: {target_url}")
    try:
        cleaned_text = scrape_url(target_url)
    except Exception as e:
        logger.error("Failed to scrape URL: %s", str(e))
        print(f"Error scraping {target_url}: {e}")
        sys.exit(1)

    print(f"Successfully scraped content ({len(cleaned_text)} characters).")

    # 2. Determine file path and save
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = args.filename or derive_domain_filename(target_url)
    out_path = out_dir / filename

    header_metadata = f"Source URL: {target_url}\nScraped for Project: {args.project}\n\n"
    full_content = header_metadata + cleaned_text

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(full_content)

    print(f"2. Saved cleaned text to: {out_path}")

    # 3. Run standard ingestion pipeline
    print(f"3. Running ingestion pipeline for project '{args.project}'...")
    ingest_res = ingest_document(
        filepath=out_path,
        project_id=args.project,
        source_url=target_url,
    )

    print("-" * 60)
    print("INGESTION RESULT:")
    print(f"  - Document ID:   {ingest_res.doc_id}")
    print(f"  - Filename:      {ingest_res.filename}")
    print(f"  - Chunk Count:   {ingest_res.chunk_count}")
    print(f"  - Quarantined:   {ingest_res.quarantined}")
    if ingest_res.quarantine_reason:
        print(f"  - Quarantine Reason: {ingest_res.quarantine_reason}")
    print(f"  - Vector Index:  data/indexes/{args.project}/index.faiss")

    # 4. Quick verification search
    print("4. Verification retrieval test...")
    results = search(project_id=args.project, query="overview about project", top_k=2)
    if results:
        print(f"  Top retrieved chunk (score: {results[0].score:.4f}):")
        preview = results[0].content[:160].replace("\n", " ")
        print(f"  \"{preview}...\"")
    print("=" * 60)
    print("Scraping and ingestion completed successfully!")


if __name__ == "__main__":
    main()

