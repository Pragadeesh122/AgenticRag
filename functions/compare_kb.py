import json
import logging
from functions.portfolio import portfolio
from functions.local_kb import query_local_kb

logger = logging.getLogger("compare-kb")


def compare_kb(query: str) -> str:
    logger.info(f"comparing both KBs for: '{query}'")

    pinecone_result = portfolio(query)
    faiss_result = query_local_kb(query)

    comparison = {
        "query": query,
        "pinecone": pinecone_result,
        "faiss": faiss_result,
    }

    logger.info("comparison complete")
    return json.dumps(comparison, indent=2)
