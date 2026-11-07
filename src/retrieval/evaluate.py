import json
from pathlib import Path

import psycopg
from sentence_transformers import SentenceTransformer
from pgvector.psycopg import register_vector


EVALUATION_FILE = Path(
    "data/evaluation_queries.json"
)

DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "knowledge_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

TOP_K = 5


def load_evaluation_queries():
    with open(
        EVALUATION_FILE,
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


def retrieve_documents(
    connection,
    query_embedding,
    top_k
):
    sql = """
        SELECT
            chunk_id,
            document_id,
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

        return cursor.fetchall()


def evaluate_query(
    connection,
    model,
    query,
    expected_document_id
):
    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    )

    results = retrieve_documents(
        connection,
        query_embedding,
        TOP_K
    )

    retrieved_document_ids = [
        row[1]
        for row in results
    ]

    hit = (
        expected_document_id
        in retrieved_document_ids
    )

    rank = None

    if hit:
        rank = (
            retrieved_document_ids.index(
                expected_document_id
            )
            + 1
        )

    return results, hit, rank


def main():
    evaluation_queries = (
        load_evaluation_queries()
    )

    print(
        f"Loaded {len(evaluation_queries)} "
        f"evaluation queries."
    )

    print(
        f"Loading model: {MODEL_NAME}"
    )

    model = SentenceTransformer(
        MODEL_NAME
    )

    connection = connect_to_database()

    total_queries = len(evaluation_queries)

    hits = 0

    reciprocal_rank_sum = 0

    for index, item in enumerate(
        evaluation_queries,
        start=1
    ):
        query = item["query"]

        expected_document_id = (
            item["expected_document_id"]
        )

        results, hit, rank = evaluate_query(
            connection,
            model,
            query,
            expected_document_id
        )

        print("\n" + "=" * 80)

        print(
            f"Query {index}: {query}"
        )

        print(
            f"Expected document: "
            f"{expected_document_id}"
        )

        print("\nRetrieved results:")

        for result_rank, row in enumerate(
            results,
            start=1
        ):
            chunk_id = row[0]
            document_id = row[1]
            topic = row[2]
            similarity = row[3]

            print(
                f"{result_rank}. "
                f"{chunk_id} | "
                f"{document_id} | "
                f"{topic} | "
                f"similarity="
                f"{similarity:.4f}"
            )

        if hit:
            hits += 1

            reciprocal_rank_sum += (
                1 / rank
            )

            print(
                f"\nResult: HIT "
                f"(rank {rank})"
            )

        else:
            print("\nResult: MISS")

    connection.close()

    hit_at_k = (
        hits / total_queries
        if total_queries
        else 0
    )

    mrr = (
        reciprocal_rank_sum
        / total_queries
        if total_queries
        else 0
    )

    print("\n" + "=" * 80)

    print("FINAL EVALUATION")

    print(
        f"Queries: {total_queries}"
    )

    print(
        f"Hits: {hits}"
    )

    print(
        f"Misses: "
        f"{total_queries - hits}"
    )

    print(
        f"Hit@{TOP_K}: "
        f"{hit_at_k:.2%}"
    )

    print(
        f"MRR: {mrr:.4f}"
    )


if __name__ == "__main__":
    main()