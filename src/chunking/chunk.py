import json
from pathlib import Path


CLEANED_DIR = Path("data/cleaned")
PROCESSED_DIR = Path("data/processed")

CHUNK_SIZE = 250
CHUNK_OVERLAP = 50


def load_document(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def split_into_chunks(text, chunk_size, overlap):
    words = text.split()

    chunks = []

    start = 0

    while start < len(words):
        end = start + chunk_size

        chunk_words = words[start:end]

        chunk_text = " ".join(chunk_words)

        chunks.append(chunk_text)

        if end >= len(words):
            break

        start = end - overlap

    return chunks


def create_chunk_records(document):
    content = document.get("content", "")

    chunks = split_into_chunks(
        content,
        CHUNK_SIZE,
        CHUNK_OVERLAP
    )

    chunk_records = []

    for index, chunk_text in enumerate(chunks, start=1):
        chunk_record = {
            "chunk_id": (
                f"{document['document_id']}_chunk_{index:03d}"
            ),
            "document_id": document["document_id"],
            "chunk_index": index,
            "text": chunk_text,
            "word_count": len(chunk_text.split()),
            "source_url": document["url"],
            "title": document["title"],
            "source_domain": document["source_domain"],
            "source_type": document["source_type"],
            "topic": document["topic"]
        }

        chunk_records.append(chunk_record)

    return chunk_records


def save_chunks(all_chunks):
    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = PROCESSED_DIR / "chunks.json"

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            all_chunks,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(f"Saved chunks to: {output_file}")


def main():
    cleaned_files = sorted(
        CLEANED_DIR.glob("document_*.json")
    )

    print(
        f"Found {len(cleaned_files)} cleaned documents."
    )

    all_chunks = []

    for file_path in cleaned_files:
        document = load_document(file_path)

        chunks = create_chunk_records(document)

        all_chunks.extend(chunks)

        print(
            f"{document['document_id']}: "
            f"{len(chunks)} chunks"
        )

    save_chunks(all_chunks)

    print("\nChunking finished.")
    print(f"Documents processed: {len(cleaned_files)}")
    print(f"Total chunks: {len(all_chunks)}")
    print(f"Chunk size: {CHUNK_SIZE} words")
    print(f"Chunk overlap: {CHUNK_OVERLAP} words")


if __name__ == "__main__":
    main()