import json
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector


DATA_FILE = Path("data/processed/embedded_chunks.json")

DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "knowledge_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres"


def load_embedded_chunks():
    with open(
        DATA_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


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


def insert_chunks(connection, chunks):
    insert_query = """
        INSERT INTO chunks (
            chunk_id,
            document_id,
            chunk_index,
            text,
            word_count,
            source_url,
            title,
            source_domain,
            source_type,
            topic,
            embedding_model,
            embedding_dimension,
            embedding
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s
        )
        ON CONFLICT (chunk_id)
        DO UPDATE SET
            text = EXCLUDED.text,
            word_count = EXCLUDED.word_count,
            source_url = EXCLUDED.source_url,
            title = EXCLUDED.title,
            source_domain = EXCLUDED.source_domain,
            source_type = EXCLUDED.source_type,
            topic = EXCLUDED.topic,
            embedding_model = EXCLUDED.embedding_model,
            embedding_dimension = EXCLUDED.embedding_dimension,
            embedding = EXCLUDED.embedding;
    """

    inserted = 0

    with connection.cursor() as cursor:

        for chunk in chunks:
            cursor.execute(
                insert_query,
                (
                    chunk["chunk_id"],
                    chunk["document_id"],
                    chunk["chunk_index"],
                    chunk["text"],
                    chunk["word_count"],
                    chunk["source_url"],
                    chunk["title"],
                    chunk["source_domain"],
                    chunk["source_type"],
                    chunk["topic"],
                    chunk["embedding_model"],
                    chunk["embedding_dimension"],
                    chunk["embedding"]
                )
            )

            inserted += 1

    connection.commit()

    return inserted


def verify_database(connection):
    with connection.cursor() as cursor:

        cursor.execute(
            "SELECT COUNT(*) FROM chunks;"
        )

        total_rows = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT
                chunk_id,
                document_id,
                topic,
                embedding_dimension
            FROM chunks
            ORDER BY id
            LIMIT 5;
            """
        )

        sample_rows = cursor.fetchall()

    print("\nDatabase verification:")
    print(f"Stored chunks: {total_rows}")

    print("\nSample rows:")

    for row in sample_rows:
        print(row)


def main():
    chunks = load_embedded_chunks()

    print(
        f"Loaded {len(chunks)} embedded chunks."
    )

    connection = connect_to_database()

    print("Connected to PostgreSQL.")

    inserted = insert_chunks(
        connection,
        chunks
    )

    print(
        f"Processed {inserted} chunks."
    )

    verify_database(connection)

    connection.close()

    print("\nDatabase loading finished.")


if __name__ == "__main__":
    main()