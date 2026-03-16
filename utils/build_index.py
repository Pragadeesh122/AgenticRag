"""Run this script to build the FAISS index from PDFs in the data/ folder."""

import logging
from utils.pdf_loader import load_pdfs
from functions.local_kb import build_index

logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")
logger = logging.getLogger("build-index")


def main():
    try:
        documents = load_pdfs("data")
    except Exception as e:
        logger.error(f"failed to load PDFs: {e}")
        return

    if not documents:
        print("No documents found in data/")
        return

    print(f"Loaded {len(documents)} chunks, building index...")
    try:
        build_index(documents)
        print("Done! Index saved to data/faiss.index")
    except Exception as e:
        logger.error(f"failed to build index: {e}")


if __name__ == "__main__":
    main()
