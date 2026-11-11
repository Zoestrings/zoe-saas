"""Unit tests for scrape_and_ingest script functions."""

import sys
from pathlib import Path
import pytest

# Add scripts directory to path for import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from scrape_and_ingest import clean_html_content, derive_domain_filename


@pytest.mark.automated
def test_derive_domain_filename():
    assert derive_domain_filename("https://www.hummingbirdco.io") == "hummingbirdco_io_info.txt"
    assert derive_domain_filename("https://www.hummingbirdco.io/about") == "hummingbirdco_io_info.txt"
    assert derive_domain_filename("https://solana.com/staking?ref=123") == "solana_com_info.txt"
    assert derive_domain_filename("http://example.org:8080/path") == "example_org_info.txt"


@pytest.mark.automated
def test_clean_html_content_strips_boilerplate():
    sample_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hummingbird Network</title>
        <meta name="description" content="AI data intelligence platform">
        <style>body { color: red; }</style>
        <script>alert('hack');</script>
    </head>
    <body>
        <header><nav><a href="#">Home</a></nav></header>
        <main>
            <h1>Welcome to Hummingbird</h1>
            <p>Hummingbird tokenizes data intelligence through AI agents.</p>
        </main>
        <footer>Copyright 2026 Hummingbird All Rights Reserved</footer>
    </body>
    </html>
    """

    cleaned = clean_html_content(sample_html)
    assert "Title: Hummingbird Network" in cleaned
    assert "Description: AI data intelligence platform" in cleaned
    assert "Welcome to Hummingbird" in cleaned
    assert "Hummingbird tokenizes data intelligence through AI agents." in cleaned
    assert "alert('hack')" not in cleaned
    assert "Copyright 2026" not in cleaned
    assert "Home" not in cleaned

