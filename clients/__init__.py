import os
from dotenv import load_dotenv
from pinecone import Pinecone
from minio import Minio
from llm import build_llm_client

load_dotenv()

_IS_PRODUCTION = os.getenv("APP_ENV") == "production"

# Provider-agnostic LLM client (LiteLLM-backed).
llm_client = build_llm_client()
# Temporary backward-compat alias for older imports.
openai_client = llm_client
pinecone_client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

if _IS_PRODUCTION:
    _minio_access = os.environ["MINIO_ACCESS_KEY"]
    _minio_secret = os.environ["MINIO_SECRET_KEY"]
else:
    _minio_access = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    _minio_secret = os.getenv("MINIO_SECRET_KEY", "minioadmin")

minio_client = Minio(
    os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    access_key=_minio_access,
    secret_key=_minio_secret,
    secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
)
