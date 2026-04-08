import logging
import os
from dotenv import load_dotenv
from clients import llm_client, pinecone_client
from llm.response_utils import extract_first_embedding

load_dotenv()

logger = logging.getLogger("portfolio-agent")
EMBEDDING_MODEL = os.getenv("DENSE_EMBEDDING_MODEL", "text-embedding-3-large")

SCHEMA = {
    "type": "function",
    "function": {
        "name": "portfolio",
        "description": "Use this function whenever a question is asked about an individual named Pragadeesh",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search about Pragadeesh",
                },
            },
            "required": ["query"],
        },
    },
}

CACHEABLE = True


def portfolio(query: str) -> list:
    try:
        embedding = llm_client.embeddings.create(
            input=query, model=EMBEDDING_MODEL
        )
        query_vector = extract_first_embedding(embedding)
    except Exception as e:
        logger.error(f"embedding failed: {e}")
        return [{"error": f"Embedding failed: {e}"}]

    try:
        index = pinecone_client.Index("pragadeesh")
        results = index.query(vector=query_vector, top_k=5, include_metadata=True)
    except Exception as e:
        logger.error(f"pinecone query failed: {e}")
        return [{"error": f"Pinecone query failed: {e}"}]

    cleaned_result = []
    for result in results["matches"]:
        metadata = result.get("metadata", {})
        cleaned_result.append(
            {"content": metadata.get("text"), "source": metadata.get("source")}
        )
    return cleaned_result
