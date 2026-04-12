# RAG Evaluation Harness

Evaluate retrieval quality and answer generation for the AgenticRAG pipeline.

## Quick start

```bash
# Retrieval metrics only (no LLM judge, fast)
uv run python evals/run_eval.py --dataset smoke --skip-judge

# Full evaluation with LLM-as-judge scoring
uv run python evals/run_eval.py --dataset smoke

# Use a specific judge model
uv run python evals/run_eval.py --dataset smoke --judge-model gpt-4o
```

## What it does

1. Creates an ephemeral project in the database
2. Uploads and ingests documents from the dataset into Pinecone
3. Runs each query through the retrieval pipeline
4. Computes retrieval metrics: Recall@k, MRR, NDCG@k, substring recall
5. (Optional) Generates answers via `project_chat_stream` and scores them with an LLM judge
6. Writes JSON + markdown reports to `evals/reports/`
7. Cleans up the ephemeral project (Pinecone namespace, DB rows, MinIO objects)

## Prerequisites

- Running PostgreSQL, Redis, Pinecone, and MinIO (the standard docker-compose stack)
- Environment variables configured (`.env`)
- For judge evaluation: an LLM API key

## Metrics

### Retrieval
- **Recall@k** — fraction of expected documents found in top-k results
- **MRR** — reciprocal rank of the first relevant result
- **NDCG@k** — normalized discounted cumulative gain
- **Substring Recall** — fraction of expected substrings found in retrieved chunks

### Answer Quality (LLM Judge)
- **Faithfulness** — claims grounded in retrieved context (1-5)
- **Completeness** — covers all expected mentions (1-5)
- **Hallucination** — free of unsupported or incorrect claims (1-5)
- **Format Adherence** — matches expected output format (1-5)

## Adding datasets

Create a new directory under `evals/datasets/<name>/` with:
- `documents/` — files to ingest (md, txt, pdf, csv, docx)
- `queries.jsonl` — one JSON object per line (see `smoke/queries.jsonl` for schema)

## Reports

Reports are written to `evals/reports/` (gitignored). Each run produces:
- `<run_id>.json` — structured data for programmatic analysis
- `<run_id>.md` — human-readable summary with per-query drill-down
