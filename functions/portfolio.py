from dotenv import load_dotenv
from clients import openai_client, pinecone_client

load_dotenv()


def portfolio(query: str) -> list:
    embedding = openai_client.embeddings.create(
        input=query, model="text-embedding-3-large"
    )
    query_vector = embedding.data[0].embedding

    index = pinecone_client.Index("pragadeesh")
    results = index.query(vector=query_vector, top_k=5, include_metadata=True)

    cleaned_result = []

    for result in results["matches"]:
        metadata = result.get("metadata")
        cleaned_result.append(
            {"content": metadata.get("text"), "source": metadata.get("source")}
        )
    return cleaned_result
