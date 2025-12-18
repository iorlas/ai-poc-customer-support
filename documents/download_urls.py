#!/usr/bin/env python3
"""Download URLs and convert to markdown for RAG indexing."""

import re
from pathlib import Path
from urllib.parse import urlparse

import structlog
import trafilatura
from patchright.sync_api import sync_playwright

# Logging setup
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
)
logger = structlog.get_logger(__name__)

# Hardcoded URL list - edit this list to add/remove URLs
URLS: list[str] = [
    # "https://ajet.com/en/frequently-asked-questions",
    # "https://ajet.com/en/services/free-check-in",
    # "https://ajet.com/en/services/seat-selection",
    # "https://ajet.com/en/services/excess-baggage",
    # "https://ajet.com/en/services/cip-lounge",
    # "https://ajet.com/en/services/sports-equipment",
    # "https://ajet.com/en/services/ajet-cafe",
    # "https://ajet.com/en/corporate/agency-information",
    # "https://ajet.com/en/corporate/rules-and-conditions/legal-notice",
    # "https://ajet.com/en/corporate/rules-and-conditions/privacy-and-cookie-policy",
    # "https://ajet.com/en/corporate/rules-and-conditions/reservation-and-ticketing",
    # "https://ajet.com/en/corporate/rules-and-conditions/free-check-in",
    # "https://ajet.com/en/corporate/rules-and-conditions/baggage",
    # "https://ajet.com/en/corporate/rules-and-conditions/seat-selection",
    # "https://ajet.com/en/corporate/rules-and-conditions/meal-selection",
    # "https://ajet.com/en/corporate/rules-and-conditions/miles-and-smiles",
    # "https://ajet.com/en/corporate/rules-and-conditions/cip-lounge",
    # "https://ajet.com/en/corporate/rules-and-conditions/infantand-child-passengers",
    # "https://ajet.com/en/corporate/rules-and-conditions/special-passenger-discounts",
    # "https://ajet.com/en/corporate/rules-and-conditions/passengers-with-special-needs",
    # "https://ajet.com/en/corporate/rules-and-conditions/pet",
    # "https://ajet.com/en/corporate/rules-and-conditions/fare-notes",
    # "https://ajet.com/en/corporate/rules-and-conditions/excess-baggage",
    # "https://ajet.com/en/corporate/rules-and-conditions/sports-equipment",
    "https://ajet.com/en/contact",
    # Add more URLs here
]

# Local HTML files to process (path, source_url for metadata)
LOCAL_FILES: list[tuple[str, str]] = [
    # ("/path/to/file.html", "https://example.com/source-url"),
]


def url_to_filename(url: str) -> str:
    """Convert URL to a safe, readable filename.

    Example: https://ajet.com/en/faq -> ajet_com_en_faq.md
    """
    parsed = urlparse(url)
    domain = parsed.netloc.replace(".", "_")
    path = parsed.path.strip("/").replace("/", "_")
    slug = re.sub(r"[^a-zA-Z0-9_]", "", f"{domain}_{path}" if path else domain)
    return f"{slug}.md"


def fetch_with_patchright(url: str) -> str | None:
    """Fetch URL using Patchright (undetected Playwright fork)."""
    logger.info("Fetching URL with Patchright", url=url)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            page.goto(url, timeout=60000)
            # Wait for main content to load (SPA apps need this)
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)  # Extra time for JS to render
            html = page.content()
            return html
        except Exception as e:
            logger.error("Patchright fetch failed", url=url, error=str(e))
            return None
        finally:
            browser.close()


def extract_markdown(html: str, url: str) -> str | None:
    """Extract markdown content from HTML using trafilatura."""
    markdown = trafilatura.extract(
        html,
        url=url,
        output_format="markdown",
        include_tables=True,
        include_links=True,
    )

    if markdown is None:
        logger.error("Failed to extract content", url=url)
        return None

    return markdown


def process_local_file(file_path: str, url: str) -> str | None:
    """Process a local HTML file."""
    logger.info("Processing local file", path=file_path)

    path = Path(file_path)
    if not path.exists():
        logger.error("File not found", path=file_path)
        return None

    html = path.read_text(encoding="utf-8")
    return extract_markdown(html, url)


def main() -> None:
    """Process all URLs and local files, save as markdown."""
    output_dir = Path(__file__).parent

    total = len(URLS) + len(LOCAL_FILES)
    logger.info("Starting document processing", urls=len(URLS), local_files=len(LOCAL_FILES))

    success_count = 0

    # Process remote URLs
    for url in URLS:
        try:
            html = fetch_with_patchright(url)
            if html is None:
                continue

            content = extract_markdown(html, url)
            if content is None:
                continue

            filename = url_to_filename(url)
            output_path = output_dir / filename

            full_content = f"<!-- Source: {url} -->\n\n{content}"
            output_path.write_text(full_content, encoding="utf-8")

            logger.info("Saved document", filename=filename, chars=len(content))
            success_count += 1

        except Exception as e:
            logger.error("Failed to process URL", url=url, error=str(e))

    # Process local files
    for file_path, url in LOCAL_FILES:
        try:
            content = process_local_file(file_path, url)
            if content is None:
                continue

            filename = url_to_filename(url)
            output_path = output_dir / filename

            full_content = f"<!-- Source: {url} -->\n\n{content}"
            output_path.write_text(full_content, encoding="utf-8")

            logger.info("Saved document", filename=filename, chars=len(content))
            success_count += 1

        except Exception as e:
            logger.error("Failed to process local file", path=file_path, error=str(e))

    logger.info("Processing complete", success=success_count, failed=total - success_count)


if __name__ == "__main__":
    main()
