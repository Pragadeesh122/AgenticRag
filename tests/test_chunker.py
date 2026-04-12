"""Unit tests for pipeline/chunker.py — all functions are pure (no I/O)."""

from pipeline.chunker import (
    _clean_text,
    _remove_repeated_lines,
    _select_strategy,
    _split_recursive,
    _find_sentence_start,
    _apply_overlap,
    chunk_pages,
    SEPARATORS,
)


# --- _clean_text ---

def test_clean_text_collapses_newlines():
    text = "Hello\n\n\n\nWorld"
    result = _clean_text(text)
    assert "\n\n\n" not in result
    assert "Hello\n\nWorld" == result


def test_clean_text_strips_pdf_page_numbers():
    text = "some content\n12\nmore content"
    result = _clean_text(text)
    assert "\n12\n" not in result
    assert "some content" in result
    assert "more content" in result


def test_clean_text_collapses_spaces():
    text = "hello    world\ttab"
    result = _clean_text(text)
    assert "hello world tab" == result


def test_clean_text_strips_line_whitespace():
    text = "  hello  \n  world  "
    result = _clean_text(text)
    assert result == "hello\nworld"


def test_clean_text_removes_repeated_headers():
    header = "CONFIDENTIAL DOCUMENT"
    text = "\n".join([header] * 5 + ["actual content"])
    result = _clean_text(text)
    assert header not in result
    assert "actual content" in result


# --- _remove_repeated_lines ---

def test_remove_repeated_lines_drops_headers():
    lines = ["PAGE HEADER"] * 5 + ["real content", "more content"]
    text = "\n".join(lines)
    result = _remove_repeated_lines(text, min_repeats=3)
    assert "PAGE HEADER" not in result
    assert "real content" in result
    assert "more content" in result


def test_remove_repeated_lines_keeps_unique():
    text = "line a\nline b\nline c"
    result = _remove_repeated_lines(text, min_repeats=3)
    assert result == text


def test_remove_repeated_lines_ignores_long_lines():
    long_line = "x" * 201
    text = "\n".join([long_line] * 5 + ["short"])
    result = _remove_repeated_lines(text, min_repeats=3)
    # Long lines are skipped by the 200-char check, so they survive
    assert long_line in result


# --- _select_strategy ---

def test_select_strategy_picks_semantic_for_headers():
    text = "# Section 1\ncontent\n# Section 2\ncontent\n# Section 3\nmore content"
    # Pad to exceed 2000 chars
    text += "\n" + ("x " * 1000)
    pages = [{"text": text}]
    assert _select_strategy(pages) == "semantic"


def test_select_strategy_picks_row_based_for_csv():
    pages = [{"text": "Columns: id, name, value\n1, foo, bar"}]
    assert _select_strategy(pages) == "row_based"


def test_select_strategy_default_recursive():
    pages = [{"text": "Just some plain prose without any special markers."}]
    assert _select_strategy(pages) == "recursive"


def test_select_strategy_needs_enough_headers_and_length():
    # 3 headers but short text -> still recursive
    text = "# A\ncontent\n# B\ncontent\n# C\ncontent"
    pages = [{"text": text}]
    assert len("".join(p["text"] for p in pages)) < 2000
    assert _select_strategy(pages) == "recursive"


# --- _split_recursive ---

def test_split_recursive_respects_max_size():
    text = "a" * 5000
    chunks = _split_recursive(text, max_size=2000)
    for chunk in chunks:
        assert len(chunk) <= 2000


def test_split_recursive_prefers_paragraph_break():
    part1 = "First paragraph. " * 50  # ~900 chars
    part2 = "Second paragraph. " * 50
    text = part1.strip() + "\n\n" + part2.strip()
    chunks = _split_recursive(text, max_size=1000)
    assert len(chunks) >= 2
    # The split should occur at the paragraph boundary
    assert chunks[0].strip().endswith("First paragraph.")
    assert "Second paragraph." in chunks[1]


def test_split_recursive_hard_split_fallback():
    # No separators at all — continuous characters
    text = "x" * 5000
    chunks = _split_recursive(text, max_size=2000)
    assert len(chunks) >= 3
    for chunk in chunks:
        assert len(chunk) <= 2000


def test_split_recursive_returns_short_text_as_is():
    text = "short text"
    chunks = _split_recursive(text, max_size=2000)
    assert chunks == ["short text"]


# --- _find_sentence_start ---

def test_find_sentence_start_finds_period():
    text = "word. Then new"
    idx = _find_sentence_start(text)
    assert text[idx:].startswith("Then")


def test_find_sentence_start_finds_question_mark():
    text = "Really? Yes it does"
    idx = _find_sentence_start(text)
    assert text[idx:].startswith("Yes")


def test_find_sentence_start_falls_back_to_newline():
    text = "no punctuation\nnext line"
    idx = _find_sentence_start(text)
    assert text[idx:].startswith("next")


def test_find_sentence_start_returns_zero_when_no_boundary():
    text = "no boundary here"
    assert _find_sentence_start(text) == 0


# --- _apply_overlap ---

def test_apply_overlap_adds_previous_tail():
    chunks = [
        {"text": "A" * 1500, "page_number": 1, "source": "test.pdf", "chunk_index": 0},
        {"text": "B" * 1500, "page_number": 1, "source": "test.pdf", "chunk_index": 1},
    ]
    result = _apply_overlap(chunks, chunk_size=2000, overlap=200)
    assert len(result) == 2
    # Second chunk should now start with some A's from the first chunk
    assert result[1]["text"].startswith("A")
    assert "B" in result[1]["text"]


def test_apply_overlap_respects_size_ceiling():
    # Make chunks where prepending overlap would exceed 1.5x chunk_size
    chunk_size = 500
    chunks = [
        {"text": "A" * 500, "page_number": 1, "source": "test.pdf", "chunk_index": 0},
        {"text": "B" * 700, "page_number": 1, "source": "test.pdf", "chunk_index": 1},
    ]
    result = _apply_overlap(chunks, chunk_size=chunk_size, overlap=200)
    # 700 + 200 = 900 > 750 (1.5 * 500), so overlap should NOT be prepended
    assert result[1]["text"] == "B" * 700


def test_apply_overlap_single_chunk_unchanged():
    chunks = [{"text": "only one", "page_number": 1, "source": "test.pdf", "chunk_index": 0}]
    result = _apply_overlap(chunks, chunk_size=2000, overlap=200)
    assert result == chunks


# --- chunk_pages ---

def test_chunk_pages_empty_input():
    chunks, strategy = chunk_pages([])
    assert chunks == []
    assert strategy == "none"


def test_chunk_pages_whitespace_only_pages():
    pages = [{"text": "   \n\n  ", "page_number": 1, "source": "test.pdf"}]
    chunks, strategy = chunk_pages(pages)
    assert chunks == []
    assert strategy == "none"


def test_chunk_pages_reindexes_after_filter():
    # Create pages that produce some tiny chunks that get filtered out
    pages = [
        {"text": "A" * 2500, "page_number": 1, "source": "test.pdf"},
        {"text": "B" * 2500, "page_number": 2, "source": "test.pdf"},
    ]
    chunks, _ = chunk_pages(pages, chunk_size=2000, chunk_overlap=0)
    # After filtering tiny chunks (<20 chars), indices should be sequential
    indices = [c["chunk_index"] for c in chunks]
    assert indices == list(range(len(chunks)))


def test_chunk_pages_recursive_end_to_end():
    text = "This is a test document. " * 200  # ~5000 chars
    pages = [{"text": text, "page_number": 1, "source": "test.pdf"}]
    chunks, strategy = chunk_pages(pages, chunk_size=2000, chunk_overlap=0, strategy="recursive")
    assert strategy == "recursive"
    assert len(chunks) >= 2
    for chunk in chunks:
        assert "text" in chunk
        assert "page_number" in chunk
        assert "source" in chunk
        assert "chunk_index" in chunk


def test_chunk_pages_semantic_end_to_end():
    sections = [
        "# Introduction\nThis is the introduction section with enough text to matter.",
        "# Methods\nThese are the methods used in the study with sufficient detail.",
        "# Results\nHere are the results of the experiment described above.",
    ]
    text = "\n".join(sections)
    # Pad to exceed 2000 chars for strategy auto-selection
    text += "\n" + "Extra content. " * 150
    pages = [{"text": text, "page_number": 1, "source": "paper.md"}]
    chunks, strategy = chunk_pages(pages, chunk_size=2000, chunk_overlap=0)
    assert strategy == "semantic"
    assert len(chunks) >= 1
    # All chunks should have required fields
    for chunk in chunks:
        assert "text" in chunk
        assert chunk["source"] == "paper.md"


def test_chunk_pages_row_based_passthrough():
    pages = [
        {"text": "Columns: id, name, email\n1, Alice, alice@example.com", "page_number": 1, "source": "data.csv"},
        {"text": "2, Bob, bob@example.com\n3, Carol, carol@example.com", "page_number": 2, "source": "data.csv"},
    ]
    chunks, strategy = chunk_pages(pages, strategy="row_based")
    assert strategy == "row_based"
    # Row-based should keep pages as-is (both exceed the 20-char filter)
    assert len(chunks) == 2


def test_chunk_pages_forced_strategy_overrides_auto():
    pages = [{"text": "Just plain text. " * 50, "page_number": 1, "source": "test.txt"}]
    chunks, strategy = chunk_pages(pages, strategy="semantic")
    assert strategy == "semantic"
