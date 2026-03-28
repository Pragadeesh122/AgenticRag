"""Dense + sparse embedding generation for hybrid search."""

import logging
from clients import openai_client, pinecone_client

logger = logging.getLogger("pipeline.embedder")

DENSE_MODEL = "text-embedding-3-large"
DENSE_DIMENSION = 3072
SPARSE_MODEL = "pinecone-sparse-english-v0"

# Max texts per API call (Pinecone sparse limit is 96)
OPENAI_BATCH_SIZE = 96


def embed_dense(texts: list[str]) -> list[list[float]]:
    """Generate dense embeddings via OpenAI text-embedding-3-large.

    Handles batching for large lists.
    """
    all_embeddings = []

    for i in range(0, len(texts), OPENAI_BATCH_SIZE):
        batch = texts[i : i + OPENAI_BATCH_SIZE]
        response = openai_client.embeddings.create(input=batch, model=DENSE_MODEL)
        batch_embeddings = [e.embedding for e in response.data]
        all_embeddings.extend(batch_embeddings)
        logger.info(
            f"dense batch {i // OPENAI_BATCH_SIZE + 1}: "
            f"{len(batch)} texts embedded"
        )

    return all_embeddings


def embed_sparse(texts: list[str]) -> list[dict]:
    """Generate sparse embeddings via Pinecone's inference API.

    Returns list of {"indices": [...], "values": [...]}
    """
    all_sparse = []

    for i in range(0, len(texts), OPENAI_BATCH_SIZE):
        batch = texts[i : i + OPENAI_BATCH_SIZE]
        response = pinecone_client.inference.embed(
            model=SPARSE_MODEL,
            inputs=batch,
            parameters={"input_type": "passage"},
        )
        for embedding in response.data:
            all_sparse.append({
                "indices": embedding.sparse_indices,
                "values": embedding.sparse_values,
            })
        logger.info(
            f"sparse batch {i // OPENAI_BATCH_SIZE + 1}: "
            f"{len(batch)} texts embedded"
        )

    return all_sparse


def embed_query_dense(query: str) -> list[float]:
    """Embed a single query string with the dense model."""
    response = openai_client.embeddings.create(input=query, model=DENSE_MODEL)
    return response.data[0].embedding


def embed_query_sparse(query: str) -> dict:
    """Embed a single query string with the sparse model."""
    response = pinecone_client.inference.embed(
        model=SPARSE_MODEL,
        inputs=[query],
        parameters={"input_type": "query"},
    )
    embedding = response.data[0]
    return {
        "indices": embedding.sparse_indices,
        "values": embedding.sparse_values,
    }
