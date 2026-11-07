import sys

import psycopg
from sentence_transformers import SentenceTransformer
from pgvector.psycopg import register_vector


DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "knowledge_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 5


def connect_to_database():
    connection = psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    register_vector(connection)

    return connection


def load_model():
    print(f"Loading embedding model: {MODEL_NAME}")

    model = SentenceTransformer(MODEL_NAME)

    return model


def embed_query(model, query):
    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    )

    return query_embedding


def retrieve_chunks(connection, query_embedding, top_k=TOP_K):
    sql = """
        SELECT
            chunk_id,
            document_id,
            text,
            source_url,
            title,
            topic,
            1 - (embedding <=> %s) AS similarity
        FROM chunks
        ORDER BY embedding <=> %s
        LIMIT %s;
    """

    with connection.cursor() as cursor:
        cursor.execute(
            sql,
            (
                query_embedding,
                query_embedding,
                top_k
            )
        )

        results = cursor.fetchall()

    return results


def print_results(results):
    print("\nTop retrieved chunks:\n")

    for rank, row in enumerate(results, start=1):
        (
            chunk_id,
            document_id,
            text,
            source_url,
            title,
            topic,
            similarity
        ) = row

        print("=" * 80)
        print(f"Rank: {rank}")
        print(f"Chunk ID: {chunk_id}")
        print(f"Document ID: {document_id}")
        print(f"Topic: {topic}")
        print(f"Title: {title}")
        print(f"Similarity: {similarity:.4f}")
        print(f"Source: {source_url}")

        print("\nText:")
        print(text)

        print()


def main():
    if len(sys.argv) < 2:
        print(
            'Usage: python src/retrieval/search.py '
            '"your question here"'
        )
        return

    query = " ".join(sys.argv[1:])

    print(f"Query: {query}")

    model = load_model()

    query_embedding = embed_query(
        model,
        query
    )

    connection = connect_to_database()

    results = retrieve_chunks(
        connection,
        query_embedding
    )

    print_results(results)

    connection.close()


if __name__ == "__main__":
    main()