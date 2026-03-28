import os
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone
from minio import Minio

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pinecone_client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
ollama_client = OpenAI(base_url=os.getenv("OLLAMA_HOST") + "/v1", api_key="ollama")

minio_client = Minio(
    os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
    secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
)
