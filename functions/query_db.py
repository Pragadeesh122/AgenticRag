import os
import json
import re
import logging
from datetime import date, datetime
from decimal import Decimal
import psycopg2
from clients import openai_client
from prompts.sql_agent import get_sql_agent_prompt
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("sql-agent")

SCHEMA = {
    "type": "function",
    "function": {
        "name": "query_db",
        "description": (
            "Query the e-commerce database to answer questions about customers, "
            "products, orders, reviews, and categories. Use this for any question "
            "that involves structured data like sales, inventory, customer info, "
            "order history, or product reviews."
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


def _validate_query(sql: str) -> str | None:
    """Validate that the query is read-only. Returns error message or None if valid."""
    stripped = sql.strip().rstrip(";").strip()

    if not stripped.upper().startswith("SELECT"):
        return f"Only SELECT queries are allowed. Got: {stripped.split()[0]}"

    match = BLOCKED_KEYWORDS.search(stripped)
    if match:
        return f"Blocked keyword detected: {match.group()}"

    # Enforce LIMIT — add one if missing and no aggregate
    # (we don't reject, just let it through — DB user is read-only anyway)
    return None


def _generate_sql(question: str) -> str:
    """Ask the LLM to generate a SQL query for the question."""
    response = openai_client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[
            {"role": "system", "content": get_sql_agent_prompt(DB_CONFIG)},
            {"role": "user", "content": question},
        ],
    )
    sql = response.choices[0].message.content.strip()
    # Strip markdown code fences if the model wraps it
    if sql.startswith("```"):
        sql = re.sub(r"^```(?:sql)?\n?", "", sql)
        sql = re.sub(r"\n?```$", "", sql)
    return sql.strip()


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
