CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    chunk_id TEXT UNIQUE NOT NULL,
    document_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    word_count INTEGER,
    source_url TEXT,
    title TEXT,
    source_domain TEXT,
    source_type TEXT,
    topic TEXT,
    embedding_model TEXT,
    embedding_dimension INTEGER,
    embedding VECTOR(384)
);