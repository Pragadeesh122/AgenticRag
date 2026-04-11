import os
import json
import re
import logging
from datetime import date, datetime
from decimal import Decimal
import psycopg2
from clients import llm_client
from prompts.sql_agent import get_sql_agent_prompt
from dotenv import load_dotenv
from llm.response_utils import extract_first_text

load_dotenv()

logger = logging.getLogger("sql-agent")

SCHEMA = {
    "type": "function",
    "function": {
        "name": "query_db",
        "description": (
            "Query the e-commerce database for structured facts about customers, "
            "products, orders, reviews, and categories. Use this when the answer must come "
            "from structured relational data such as sales, inventory, customer records, or "
            "order history. Do not use it for web facts or document content. "
            "Use one query first, then decide on follow-up questions from the result; do not "
            "assume parallel DB fan-out is needed. It returns JSON with either {sql, rows, count} or {error, sql}."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The natural language question to answer from the database",
                },
            },
            "required": ["question"],
        },
    },
}

CACHEABLE = True
POLICY = {
    "execution_mode": "sequential_first",
    "max_parallel_instances": 1,
    "requires_fresh_input": True,
    "dedupe_key_fields": ("question",),
    "verification_only_after_result": True,
}

# Read-only DB connection config — uses the llm_reader user
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

# Statements that should never appear in a query
BLOCKED_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|EXECUTE|COPY)\b",
    re.IGNORECASE,
)

MAX_ROWS = 50


def _strip_sql_fences(text: str) -> str:
    sql = text.strip()
    if sql.startswith("```"):
        sql = re.sub(r"^```(?:sql)?\n?", "", sql)
        sql = re.sub(r"\n?```$", "", sql)
    return sql.strip()


def _validate_query(sql: str) -> str | None:
    """Validate that the query is read-only. Returns error message or None if valid."""
    stripped = _strip_sql_fences(sql).rstrip(";").strip()

    if not stripped:
        return "The model did not return a SQL query."

    if ";" in stripped:
        return "Only a single SELECT statement is allowed."

    if "--" in stripped or "/*" in stripped or "*/" in stripped:
        return "SQL comments are not allowed."

    upper = stripped.upper()
    if upper.startswith("WITH "):
        if "SELECT" not in upper:
            return "CTE queries must resolve to a SELECT statement."
    elif not upper.startswith("SELECT"):
        return f"Only SELECT queries are allowed. Got: {stripped.split()[0]}"

    match = BLOCKED_KEYWORDS.search(stripped)
    if match:
        return f"Blocked keyword detected: {match.group()}"

    return None


def _generate_sql(question: str) -> str:
    """Ask the LLM to generate a structured SQL payload for the question."""
    response = llm_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    f"{get_sql_agent_prompt(DB_CONFIG)}\n\n"
                    "Return a JSON object with a single key named 'sql'. "
                    "The value must be one read-only PostgreSQL SELECT query and nothing else."
                ),
            },
            {"role": "user", "content": question},
        ],
        response_format={"type": "json_object"},
    )
    raw = extract_first_text(response, "{}").strip()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("structured SQL generation returned malformed JSON")
        return ""

    return _strip_sql_fences(str(payload.get("sql", "")))


def _serialize_value(val):
    """Convert non-JSON-serializable DB values to strings."""
    if isinstance(val, (date, datetime)):
        return val.isoformat()
    if isinstance(val, Decimal):
        return float(val)
    return val


def _execute_query(sql: str) -> list[dict]:
    """Execute a read-only query and return results as a list of dicts."""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        conn.set_session(readonly=True, autocommit=True)
        with conn.cursor() as cur:
            cur.execute(sql)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchmany(MAX_ROWS)
            return [
                {col: _serialize_value(val) for col, val in zip(columns, row)}
                for row in rows
            ]
    finally:
        conn.close()


def query_db(question: str) -> dict:
    """Generate SQL from a question, validate, execute, and return results."""
    # Step 1 — LLM generates SQL
    sql = _generate_sql(question)
    logger.info(f"generated SQL: {sql}")

    # Step 2 — Validate (programmatic guardrail)
    error = _validate_query(sql)
    if error:
        logger.warning(f"query rejected: {error}")
        return {"error": error, "sql": sql}

    # Step 3 — Execute against read-only user
    try:
        results = _execute_query(sql)
        logger.info(f"query returned {len(results)} rows")
        return {"sql": sql, "rows": results, "count": len(results)}
    except psycopg2.Error as e:
        logger.error(f"query execution failed: {e}")
        return {"error": str(e), "sql": sql}
