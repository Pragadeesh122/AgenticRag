"""Run this script to build the FAISS index from PDFs in the data/ folder."""

import logging
from utils.pdf_loader import load_pdfs
from functions.local_kb import build_index

logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")


def main():
    documents = load_pdfs("data")
    if not documents:
        print("No documents found in data/")
        return

    print(f"Loaded {len(documents)} chunks, building index...")
    build_index(documents)
    print("Done! Index saved to data/faiss.index")


if __name__ == "__main__":
    main()
