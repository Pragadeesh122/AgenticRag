import os
from dotenv import load_dotenv
from pinecone import Pinecone
from minio import Minio
from llm import build_llm_client

load_dotenv()

# Provider-agnostic LLM client (LiteLLM-backed).
llm_client = build_llm_client()
# Temporary backward-compat alias for older imports.
openai_client = llm_client
pinecone_client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

minio_client = Minio(
    os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
    secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
)
