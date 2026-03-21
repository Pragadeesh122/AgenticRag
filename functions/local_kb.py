import os
import json
import logging
import faiss
import numpy as np
from clients import openai_client

logger = logging.getLogger("local-kb-agent")

INDEX_PATH = "data/faiss.index"
METADATA_PATH = "data/metadata.json"
EMBEDDING_MODEL = "text-embedding-3-large"
DIMENSION = 3072

SCHEMA = {
    "type": "function",
    "function": {
        "name": "query_local_kb",
        "description": "Search the local knowledge base for information about Citro Essential Oils Distillery Industry, essential oils, their products, processes, or any related company data.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to search the local knowledge base",
                },
            },
            "required": ["query"],
        },
    },
}

CACHEABLE = True


def build_index(documents: list[dict]):
    """
    Build a FAISS index from documents.
    Each document should be: {"text": "...", "source": "..."}
    """
    texts = [doc["text"] for doc in documents]

    response = openai_client.embeddings.create(input=texts, model=EMBEDDING_MODEL)
    embeddings = np.array([e.embedding for e in response.data], dtype=np.float32)

    index = faiss.IndexFlatL2(DIMENSION)
    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)
    with open(METADATA_PATH, "w") as f:
        json.dump(documents, f, indent=2)

    logger.info(f"built index with {len(documents)} documents")


def query_local_kb(query: str) -> list:
    if not os.path.exists(INDEX_PATH):
        return [{"error": "No local knowledge base found. Please build the index first."}]

    try:
        index = faiss.read_index(INDEX_PATH)
        with open(METADATA_PATH, "r") as f:
            documents = json.load(f)
    except Exception as e:
        logger.error(f"failed to load index/metadata: {e}")
        return [{"error": f"Failed to load knowledge base: {e}"}]

    try:
        response = openai_client.embeddings.create(input=query, model=EMBEDDING_MODEL)
        query_vector = np.array([response.data[0].embedding], dtype=np.float32)
    except Exception as e:
        logger.error(f"embedding failed: {e}")
        return [{"error": f"Embedding failed: {e}"}]

    distances, indices = index.search(query_vector, k=5)

    results = []
    for i, idx in enumerate(indices[0]):
        if idx < len(documents):
            results.append(
                {
                    "text": documents[idx]["text"],
                    "source": documents[idx].get("source", "unknown"),
                    "score": float(distances[0][i]),
                }
            )

    logger.info(f"query: '{query}' → {len(results)} results")

    return results
