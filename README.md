# news-chatbot

Local-first experimentation space for a Retrieval-Augmented Generation (RAG) news chatbot. The project is built with Python 3.13 and Poetry so that we can iterate quickly, then port the workflow to Haystack and eventually deploy to the cloud.

## Library stack

| Library | Purpose |
| --- | --- |
| `weaviate-client` | Talk to the local Weaviate instance for schema management, batching, and querying. |
| `requests` | Lightweight HTTP helper for pulling news datasets or external feeds. |
| `python-dotenv` | Load API keys and config from a `.env` file while developing locally. |
| `pandas` | Clean and transform news datasets prior to chunking and ingestion. |

All dependencies are tracked in `pyproject.toml`/`poetry.lock` and installed inside the in-project virtualenv (`.venv`).

## Phase 1 plan (manual pipeline)

1. **Environment & services**
   - Compose file for Weaviate + `text2vec-transformers` inference container (`docker-compose.yml`).
   - Health-check script (`poetry run python -m news_chatbot.health_check`) to ensure the database and module are reachable.
2. **Data acquisition**
   - Fetch a small news corpus (CSV/JSON or API pull) and normalize fields like title, published date, body text.
3. **Pre-processing**
   - Chunk long articles into passages (~500 tokens) and enrich with metadata for traceability.
4. **Ingestion**
   - Use `weaviate-client` batch insert to push passages; rely on the transformer module for vectorization.
5. **Query loop**
   - Accept a user question, run `nearText` search, and collect the top matches plus metadata.
6. **Answer generation**
   - Send retrieved passages to OpenAI for summarisation/answering and surface citations to the user.
7. **Interface**
   - Wrap the flow in a simple CLI or Streamlit prototype for conversational testing.

Once Phase 1 is stable we will recreate the flow with Haystack pipelines, then containerise for AWS deployment.

## Configuration

Set Weaviate connection details in your shell or a `.env` file:

```
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
WEAVIATE_GRPC_PORT=50051
# optional if your instance requires it
WEAVIATE_API_KEY=changeme
```

`python-dotenv` loads the file automatically when the health check (and future scripts) run.

## Running the Weaviate stack

```bash
# build/start the local vector database + embedding service
docker compose up -d

# follow logs when diagnosing startup issues
docker compose logs -f weaviate
```

The compose file persists Weaviate data under `./data/weaviate` so embeddings survive restarts.

## Getting started

```bash
# ensure the local Python matches the project
pyenv local 3.13.0

# install dependencies into the poetry-managed .venv
poetry install

# verify connectivity to Weaviate (after docker compose up)
poetry run python -m news_chatbot.health_check
```

Keep secrets (OpenAI keys, etc.) in a `.env` file; never commit it to version control.
