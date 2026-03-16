import os
import re
import logging
from pypdf import PdfReader

logger = logging.getLogger("pdf-loader")


def load_pdfs(directory: str = "data") -> list[dict]:
    """Load all PDFs from a directory and return chunked documents."""
    documents = []

    for root, _, files in os.walk(directory):
        for filename in files:
            if not filename.endswith(".pdf"):
                continue

            filepath = os.path.join(root, filename)
            reader = PdfReader(filepath)

            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""

            chunks = chunk_text(text, chunk_size=500, overlap=150)

            for chunk in chunks:
                documents.append({"text": chunk, "source": filename})

            logger.info(
                f"loaded {filename}: {len(reader.pages)} pages → {len(chunks)} chunks"
            )

    return documents


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 150) -> list[str]:
    """Split text into overlapping chunks, respecting sentence boundaries."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Overlap: keep the last portion of the current chunk
            words = current_chunk.split()
            overlap_text = " ".join(words[-overlap // 5:]) if len(words) > overlap // 5 else current_chunk
            current_chunk = overlap_text + " " + sentence
        else:
            current_chunk += (" " + sentence if current_chunk else sentence)

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
