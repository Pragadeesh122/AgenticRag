"""Text extraction from various file types using PyMuPDF, python-docx, etc."""

import csv
import io
import logging
from pathlib import Path

import pymupdf4llm

logger = logging.getLogger("pipeline.extractor")

# Supported file types → extraction method
SUPPORTED_TYPES = {"pdf", "txt", "md", "csv", "docx"}


def extract_text(file_path: str) -> list[dict]:
    """Extract text from a file, returning a list of page/section dicts.

    Returns:
        list of {"text": str, "page_number": int | None, "source": str}
    """
    path = Path(file_path)
    ext = path.suffix.lower().lstrip(".")
    filename = path.name

    if ext not in SUPPORTED_TYPES:
        raise ValueError(f"Unsupported file type: {ext}")

    if ext == "pdf":
        return _extract_pdf(file_path, filename)
    elif ext in ("txt", "md"):
        return _extract_plaintext(file_path, filename)
    elif ext == "csv":
        return _extract_csv(file_path, filename)
    elif ext == "docx":
        return _extract_docx(file_path, filename)

    return []


def _extract_pdf(file_path: str, filename: str) -> list[dict]:
    """Extract PDF text using PyMuPDF4LLM with markdown + table support."""
    pages = pymupdf4llm.to_markdown(
        file_path,
        page_chunks=True,
        table_strategy="lines",
    )

    results = []
    for page in pages:
        text = page.get("text", "").strip()
        if not text:
            continue
        page_num = page.get("metadata", {}).get("page", None)
        results.append({
            "text": text,
            "page_number": page_num,
            "source": filename,
        })

    logger.info(f"extracted {len(results)} pages from PDF '{filename}'")
    return results


def _extract_plaintext(file_path: str, filename: str) -> list[dict]:
    """Read plain text or markdown files."""
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        return []

    logger.info(f"extracted text from '{filename}' ({len(text)} chars)")
    return [{"text": text, "page_number": None, "source": filename}]


def _extract_csv(file_path: str, filename: str) -> list[dict]:
    """Convert CSV rows into text chunks with column headers as context."""
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return []

        headers = reader.fieldnames
        rows = list(reader)

    if not rows:
        return []

    # Group rows into chunks of 20 for context
    chunk_size = 20
    results = []
    for i in range(0, len(rows), chunk_size):
        batch = rows[i : i + chunk_size]
        lines = []
        for row in batch:
            line = " | ".join(f"{h}: {row.get(h, '')}" for h in headers)
            lines.append(line)

        text = f"Columns: {', '.join(headers)}\n\n" + "\n".join(lines)
        results.append({
            "text": text,
            "page_number": None,
            "source": f"{filename} (rows {i + 1}-{i + len(batch)})",
        })

    logger.info(f"extracted {len(results)} chunks from CSV '{filename}' ({len(rows)} rows)")
    return results


def _extract_docx(file_path: str, filename: str) -> list[dict]:
    """Extract text from DOCX using python-docx, preserving heading structure as markdown."""
    from docx import Document

    doc = Document(file_path)
    parts = []

    # Map DOCX heading levels to markdown
    heading_map = {
        "Heading 1": "# ",
        "Heading 2": "## ",
        "Heading 3": "### ",
        "Heading 4": "#### ",
        "Heading 5": "##### ",
        "Heading 6": "###### ",
    }

    # Track position in document body to interleave tables
    for element in doc.element.body:
        tag = element.tag.split("}")[-1]  # Strip namespace

        if tag == "p":
            # Paragraph — check if it's a heading
            from docx.text.paragraph import Paragraph
            para = Paragraph(element, doc)
            text = para.text.strip()
            if not text:
                continue

            style_name = para.style.name if para.style else ""
            prefix = heading_map.get(style_name, "")
            parts.append(f"{prefix}{text}")

        elif tag == "tbl":
            # Table — render as markdown table
            from docx.table import Table
            table = Table(element, doc)
            rows = []
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                rows.append("| " + " | ".join(cells) + " |")
            if rows:
                # Add header separator after first row
                header_sep = "| " + " | ".join("---" for _ in table.rows[0].cells) + " |"
                rows.insert(1, header_sep)
                parts.append("\n".join(rows))

    if not parts:
        return []

    full_text = "\n\n".join(parts)
    logger.info(f"extracted text from DOCX '{filename}' ({len(full_text)} chars)")
    return [{"text": full_text, "page_number": None, "source": filename}]
