import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import time
import random

import requests
from bs4 import BeautifulSoup


SOURCES_FILE = Path("data/sources.json")
OUTPUT_DIR = Path("data/raw")
session = requests.Session()

session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/127.0 Safari/537.36"
    )
})


def load_sources():
    with open(SOURCES_FILE, "r", encoding="utf-8") as file:
        sources = json.load(file)

    return sources
def validate_sources(sources):
    seen_urls = set()

    for index, source in enumerate(sources, start=1):
        required_fields = ["url", "source_type", "topic"]

        for field in required_fields:
            if field not in source or not source[field]:
                raise ValueError(
                    f"Source #{index} is missing required field: {field}"
                )

        if source["url"] in seen_urls:
            raise ValueError(
                f"Duplicate URL found: {source['url']}"
            )

        seen_urls.add(source["url"])

    print(f"Validated {len(sources)} sources successfully.")


def collect_document(source, document_id, max_retries=3):
    url = source["url"]

    print(f"Collecting: {url}")

    for attempt in range(1, max_retries + 1):

        try:
            response = session.get(url, timeout=30)

            if response.status_code == 429:
                wait_time = 10 * attempt

                print(
                    f"Rate limited (429). "
                    f"Waiting {wait_time} seconds..."
                )

                time.sleep(wait_time)
                continue

            response.raise_for_status()

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            title = (
                soup.title.get_text(strip=True)
                if soup.title
                else "No title"
            )

            text = soup.get_text(
                separator="\n",
                strip=True
            )

            domain = urlparse(url).netloc

            document = {
                "document_id": document_id,
                "url": url,
                "title": title,
                "source_domain": domain,
                "source_type": source["source_type"],
                "topic": source["topic"],
                "content": text,
                "collected_at": datetime.now().isoformat(),
            }

            return document

        except requests.RequestException as error:

            print(
                f"Attempt {attempt}/{max_retries} failed: "
                f"{error}"
            )

            if attempt < max_retries:
                wait_time = 5 * attempt
                print(
                    f"Retrying in {wait_time} seconds..."
                )
                time.sleep(wait_time)

    print(f"Failed after {max_retries} attempts: {url}")

    return None


def save_document(document, index):
    output_file = OUTPUT_DIR / f"document_{index:03d}.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(
            document,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(f"Saved: {output_file}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sources = load_sources()
    validate_sources(sources)

    successful = 0
    failed = 0

    for index, source in enumerate(sources, start=1):

        document_id = f"doc_{index:03d}"

        document = collect_document(
            source,
            document_id
        )

        if document is None:
            failed += 1
            continue

        save_document(document, index)

        successful += 1
        delay = random.uniform(2, 4)
        print(f"Waiting {delay:.1f} seconds...\n")
        time.sleep(delay)

    print("\nCollection finished.")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")


if __name__ == "__main__":
    main()