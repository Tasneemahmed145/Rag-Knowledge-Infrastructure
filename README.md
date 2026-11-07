# Knowledge Infrastructure – EU AI Act Retrieval System

A reproducible knowledge infrastructure pipeline for collecting, cleaning, chunking, embedding, storing, retrieving, and evaluating official EU AI Act content.

The system builds a semantic search pipeline over official EU regulatory sources using Python, Sentence Transformers, PostgreSQL, and pgvector.

---

## Project Overview

This project implements an end-to-end retrieval pipeline:

```text
Official EU Sources
        ↓
Data Collection
        ↓
Cleaning & Preprocessing
        ↓
Chunking
        ↓
Embeddings
        ↓
PostgreSQL + pgvector
        ↓
Semantic Retrieval
        ↓
Quantitative Evaluation
```

The current dataset contains:

- 60 source documents
- 227 processed chunks
- 227 vector embeddings
- 384-dimensional embedding vectors

---

## Data Sources

The dataset is collected from official European Union sources, primarily:

- EU AI Act Service Desk
- European Commission – Shaping Europe’s Digital Future

The collection pipeline stores source metadata including:

- Document ID
- URL
- Title
- Source domain
- Source type
- Topic
- Collection timestamp

Raw documents are stored in:

```text
data/raw/
```

---

## Project Structure

```text
knowledge-infrastructure/
│
├── data/
│   ├── raw/
│   ├── cleaned/
│   ├── processed/
│   │   ├── chunks.json
│   │   └── embedded_chunks.json
│   ├── sources.json
│   └── evaluation_queries.json
│
├── src/
│   ├── ingestion/
│   │   └── collect.py
│   │
│   ├── preprocessing/
│   │   └── clean.py
│   │
│   ├── chunking/
│   │   └── chunk.py
│   │
│   ├── embeddings/
│   │   └── generate_embeddings.py
│   │
│   ├── database/
│   │   └── load_embeddings.py
│   │
│   └── retrieval/
│       ├── search.py
│       └── evaluate.py
│
├── docker-compose.yml
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Requirements

The project requires:

- Python 3.11+
- Git
- Docker Desktop
- WSL2 on Windows

Check the installations using:

```bash
python --version
git --version
docker --version
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Tasneemahmed145/knowledge-infrastructure.git
cd knowledge-infrastructure
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

---

## 1. Data Collection

The ingestion pipeline collects AI regulation documents and their metadata from the configured official sources.

Run:

```bash
python src/ingestion/collect.py
```

Expected result:

```text
Collection finished.
Successful: 60
Failed: 0
```

Raw documents are stored in:

```text
data/raw/
```

---

## 2. Cleaning and Preprocessing

The cleaning pipeline removes website boilerplate and navigation content while preserving the relevant regulatory text and metadata.

Run:

```bash
python src/preprocessing/clean.py
```

Expected result:

```text
Cleaning finished.
Successful: 60
Failed: 0
```

Cleaned documents are stored in:

```text
data/cleaned/
```

The raw source files are preserved and are not overwritten.

---

## 3. Chunking

Cleaned documents are divided into smaller retrieval units.

Current chunking configuration:

```text
Chunk size: 250 words
Chunk overlap: 50 words
```

The overlap helps preserve context across chunk boundaries.

Run:

```bash
python src/chunking/chunk.py
```

Current output:

```text
Documents processed: 60
Total chunks: 227
Chunk size: 250 words
Chunk overlap: 50 words
```

Chunks are stored in:

```text
data/processed/chunks.json
```

Each chunk preserves metadata including its source document, URL, title, topic, and chunk identifier.

---

## 4. Embedding Generation

The project uses:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Embedding dimension:

```text
384
```

To improve retrieval quality, the embedding input includes the document title and topic together with the chunk content.

Run:

```bash
python src/embeddings/generate_embeddings.py
```

Expected validation:

```text
Total chunks: 227
Chunks with embeddings: 227
Expected vector dimension: 384
All embedding dimensions are valid.
Embedding count matches chunk count.
```

Generated embeddings are stored in:

```text
data/processed/embedded_chunks.json
```

---

## 5. PostgreSQL and pgvector

The vector database runs using Docker.

Start PostgreSQL:

```bash
docker compose up -d
```

Verify that the container is running:

```bash
docker ps
```

The PostgreSQL container is:

```text
knowledge_postgres
```

Connect to the database:

```bash
docker exec -it knowledge_postgres psql -U postgres -d knowledge_db
```

Enable pgvector if the database is being initialized manually:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

The embedding column uses:

```text
VECTOR(384)
```

Exit PostgreSQL using:

```text
\q
```

---

## 6. Load Embeddings into PostgreSQL

Load the processed chunks and embeddings into the vector database:

```bash
python src/database/load_embeddings.py
```

Expected result:

```text
Loaded 227 embedded chunks.
Connected to PostgreSQL.
Processed 227 chunks.

Database verification:
Stored chunks: 227
```

Database storage can also be verified using:

```sql
SELECT COUNT(*) FROM chunks;
```

Expected:

```text
227
```

---

## 7. Semantic Retrieval

The retrieval system accepts natural-language queries.

Example:

```bash
python src/retrieval/search.py "What are the requirements for human oversight?"
```

The query is embedded using the same Sentence Transformer model used for the document chunks.

PostgreSQL and pgvector then perform cosine-distance vector search and return ranked results.

Example top result:

```text
Rank: 1
Topic: Human Oversight
Title: Article 14: Human oversight
Similarity: 0.6393
```

Each result includes:

- Rank
- Chunk ID
- Document ID
- Topic
- Title
- Similarity score
- Source URL
- Retrieved text

---

## 8. Retrieval Evaluation

Retrieval quality is evaluated using a fixed set of natural-language queries with expected source documents.

Run:

```bash
python src/retrieval/evaluate.py
```

Current evaluation result:

```text
Queries: 5
Hits: 5
Misses: 0
Hit@5: 100.00%
MRR: 0.7000
```

### Hit@5

Hit@5 measures whether the expected document appears within the first five retrieved results.

Current result:

```text
Hit@5 = 100%
```

### Mean Reciprocal Rank

MRR rewards the system when the expected result appears at a higher rank.

Current result:

```text
MRR = 0.7000
```

The evaluation queries are stored in:

```text
data/evaluation_queries.json
```

---

## Engineering Decisions

### Why preserve raw data?

Raw source documents are kept unchanged so that preprocessing remains reproducible and cleaning changes can be rerun without recollecting the original data.

### Why use overlapping chunks?

A 50-word overlap reduces information loss when relevant context crosses a chunk boundary.

### Why use all-MiniLM-L6-v2?

The model provides a lightweight local embedding solution with 384-dimensional vectors and is suitable for semantic retrieval without requiring a paid embedding API.

### Why include title and topic in embedding input?

Initial retrieval evaluation showed that embedding only the chunk text could cause general AI Act guidance documents to outrank the specific legal article.

Adding title and topic context improved retrieval performance while preserving the original chunk text.

### Why PostgreSQL + pgvector?

PostgreSQL provides structured metadata storage while pgvector adds vector similarity search within the same database.

This allows semantic retrieval and structured metadata to remain in one storage layer.

---

## Reproducing the Core Pipeline

With Docker running and the Python environment activated:

```bash
python src/ingestion/collect.py
python src/preprocessing/clean.py
python src/chunking/chunk.py
python src/embeddings/generate_embeddings.py

docker compose up -d

python src/database/load_embeddings.py

python src/retrieval/search.py "What are the requirements for human oversight?"
python src/retrieval/evaluate.py
```

---

## Current Milestone Status

| Component | Status |
|---|---|
| Data collection | Complete |
| Cleaning & preprocessing | Complete |
| Chunking | Complete |
| Embedding generation | Complete |
| PostgreSQL setup | Complete |
| pgvector integration | Complete |
| Vector storage | Complete |
| Semantic retrieval | Complete |
| Quantitative evaluation | Complete |

---

## Current Evaluation Summary

```text
Documents: 60
Chunks: 227
Embeddings: 227
Embedding dimensions: 384
Evaluation queries: 5
Hit@5: 100.00%
MRR: 0.7000
```