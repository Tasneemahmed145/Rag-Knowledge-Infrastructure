import json
from pathlib import Path

from sentence_transformers import SentenceTransformer


CHUNKS_FILE = Path("data/processed/chunks.json")
OUTPUT_FILE = Path("data/processed/embedded_chunks.json")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_DIMENSION = 384


def load_chunks():
    with open(
        CHUNKS_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def load_model():
    print(f"Loading embedding model: {MODEL_NAME}")

    model = SentenceTransformer(MODEL_NAME)

    return model


def generate_embeddings(model, chunks):
    texts = [
    (
        f"Title: {chunk['title']}\n"
        f"Topic: {chunk['topic']}\n"
        f"Content: {chunk['text']}"
    )
    for chunk in chunks
]

    print(
        f"Generating embeddings for "
        f"{len(texts)} chunks..."
    )

    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    return embeddings


def attach_embeddings(chunks, embeddings):
    embedded_chunks = []

    for chunk, embedding in zip(
        chunks,
        embeddings
    ):
        chunk_with_embedding = chunk.copy()

        chunk_with_embedding["embedding"] = (
            embedding.tolist()
        )

        chunk_with_embedding[
            "embedding_model"
        ] = MODEL_NAME

        chunk_with_embedding[
            "embedding_dimension"
        ] = VECTOR_DIMENSION

        embedded_chunks.append(
            chunk_with_embedding
        )

    return embedded_chunks


def save_embedded_chunks(embedded_chunks):
    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            embedded_chunks,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"Saved embeddings to: {OUTPUT_FILE}"
    )


def validate_embeddings(embedded_chunks):
    total_chunks = len(embedded_chunks)

    chunks_with_embeddings = sum(
        1
        for chunk in embedded_chunks
        if "embedding" in chunk
    )

    invalid_dimensions = [
        chunk["chunk_id"]
        for chunk in embedded_chunks
        if len(chunk["embedding"])
        != VECTOR_DIMENSION
    ]

    print("\nValidation:")
    print(f"Total chunks: {total_chunks}")
    print(
        f"Chunks with embeddings: "
        f"{chunks_with_embeddings}"
    )
    print(
        f"Expected vector dimension: "
        f"{VECTOR_DIMENSION}"
    )

    if invalid_dimensions:
        print(
            "Invalid embeddings found:",
            invalid_dimensions
        )
    else:
        print(
            "All embedding dimensions are valid."
        )

    if total_chunks == chunks_with_embeddings:
        print(
            "Embedding count matches chunk count."
        )
    else:
        print(
            "ERROR: Embedding count does not "
            "match chunk count."
        )


def main():
    chunks = load_chunks()

    print(
        f"Loaded {len(chunks)} chunks."
    )

    model = load_model()

    embeddings = generate_embeddings(
        model,
        chunks
    )

    embedded_chunks = attach_embeddings(
        chunks,
        embeddings
    )

    validate_embeddings(
        embedded_chunks
    )

    save_embedded_chunks(
        embedded_chunks
    )

    print("\nEmbedding generation finished.")


if __name__ == "__main__":
    main()