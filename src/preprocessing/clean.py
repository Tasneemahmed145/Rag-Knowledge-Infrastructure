import json
import re
from pathlib import Path


RAW_DIR = Path("data/raw")
CLEANED_DIR = Path("data/cleaned")


BOILERPLATE_LINES = {
    "Skip to main content",
    "Select your language",
    "Close",
    "Search",
    "Menu",
    "Back",
    "Previous items",
    "Next items",
    "Home",
    "See all",
    "Contact us",
    "Contact the AI Office",
    "About us",
    "Copyright notice",
    "Legal notice",
    "Privacy statement",
    "Follow the European Commission",
    "Facebook",
    "Instagram",
    "X",
    "Linkedin",
    "Other",
    "Report an IT vulnerability",
    "Languages on our websites",
    "Cookies",
    "Privacy policy",
    "Accessibility",
    "AI Act Service Desk",
    "About Directorate-General CONNECT",
}


LANGUAGE_LINES = {
    "en",
    "es",
    "de",
    "fr",
    "it",
    "pl",
    "English",
    "Spanish",
    "German",
    "French",
    "Italian",
    "Polish",
}


def load_document(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def is_navigation_number(line):
    """
    Remove standalone navigation numbers such as:
    1
    2
    3
    ...
    180

    But do not remove numbered legal paragraphs such as:
    1. The purpose of this Regulation...
    """

    return bool(re.fullmatch(r"\d+", line))


def remove_ai_act_navigation(lines, document):
    """
    Remove the large AI Act Explorer navigation section
    from AI Act Service Desk article pages.

    We keep the actual article content starting from
    the last occurrence of the article heading.
    """

    if document.get("source_domain") != "ai-act-service-desk.ec.europa.eu":
        return lines

    document_id = document.get("document_id", "")

    article_number_match = re.search(r"(\d+)", document_id)

    if not article_number_match:
        return lines

    article_number = int(article_number_match.group(1))

    target_prefix = f"Article {article_number}:"

    matching_indexes = []

    for index, line in enumerate(lines):
        if line.startswith(target_prefix):
            matching_indexes.append(index)

    if len(matching_indexes) >= 2:
        start_index = matching_indexes[-1]
        return lines[start_index:]

    return lines


def clean_text(text, document):
    lines = text.splitlines()

    cleaned_lines = []

    for line in lines:
        line = line.strip()

        # Remove empty lines
        if not line:
            continue

        # Normalize repeated whitespace
        line = re.sub(r"\s+", " ", line)

        # Remove known website boilerplate
        if line in BOILERPLATE_LINES:
            continue

        # Remove language selector items
        if line in LANGUAGE_LINES:
            continue

        # Remove standalone navigation numbers
        if is_navigation_number(line):
            continue

        cleaned_lines.append(line)

    # Remove AI Act Explorer navigation section
    cleaned_lines = remove_ai_act_navigation(
        cleaned_lines,
        document
    )

    # Remove consecutive duplicate lines
    deduplicated_lines = []

    previous_line = None

    for line in cleaned_lines:
        if line != previous_line:
            deduplicated_lines.append(line)

        previous_line = line

    return "\n".join(deduplicated_lines).strip()


def save_document(document, file_name):
    CLEANED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = CLEANED_DIR / file_name

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            document,
            file,
            ensure_ascii=False,
            indent=2
        )


def main():
    raw_files = sorted(
        RAW_DIR.glob("document_*.json")
    )

    print(
        f"Found {len(raw_files)} raw documents."
    )

    successful = 0
    failed = 0

    for file_path in raw_files:
        try:
            document = load_document(file_path)

            raw_content = document.get(
                "content",
                ""
            )

            cleaned_content = clean_text(
                raw_content,
                document
            )

            document["content"] = cleaned_content

            document["cleaning_metadata"] = {
                "raw_characters": len(raw_content),
                "cleaned_characters": len(cleaned_content),
                "removed_characters": (
                    len(raw_content)
                    - len(cleaned_content)
                ),
                "cleaning_status": "success"
            }

            save_document(
                document,
                file_path.name
            )

            successful += 1

            print(
                f"Cleaned: {file_path.name} "
                f"({len(raw_content)} -> "
                f"{len(cleaned_content)} characters)"
            )

        except Exception as error:
            failed += 1

            print(
                f"Failed: {file_path.name}"
            )

            print(
                f"Error: {error}"
            )

    print("\nCleaning finished.")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")


if __name__ == "__main__":
    main()