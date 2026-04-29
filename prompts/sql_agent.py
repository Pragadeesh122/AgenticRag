import psycopg2
from memory.redis_client import redis_client

REDIS_KEY = "sql_agent:prompt"
CACHE_TTL = 300  # 5 minutes


def _fetch_schema(db_config: dict) -> str:
    """Fetch table/column metadata from information_schema and format as markdown."""
    conn = psycopg2.connect(**db_config)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name, column_name, data_type,
                       is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """)
            columns = cur.fetchall()

            cur.execute("""
                SELECT
                    tc.table_name, kcu.column_name,
                    ccu.table_name AS foreign_table,
                    ccu.column_name AS foreign_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                    ON tc.constraint_name = ccu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public'
            """)
            fkeys = cur.fetchall()
    finally:
        conn.close()

    # Build FK lookup
    fk_map = {}
    for table, col, ftable, fcol in fkeys:
        fk_map[(table, col)] = f"→ {ftable}({fcol})"

    # Group columns by table
    tables: dict[str, list] = {}
    for table, col, dtype, nullable, default in columns:
        tables.setdefault(table, []).append((col, dtype, nullable, default))

    # Format as markdown
    lines = []
    relationships = []
    for table, cols in tables.items():
        lines.append(f"### {table}")
        lines.append("| Column | Type | Notes |")
        lines.append("|--------|------|-------|")
        for col, dtype, nullable, default in cols:
            notes = []
            if (table, col) in fk_map:
                notes.append(f"FK {fk_map[(table, col)]}")
                relationships.append(f"- {table}.{col} {fk_map[(table, col)]}")
            if default and "nextval" in str(default):
                notes.append("PK")
            if nullable == "NO" and "nextval" not in str(default or ""):
                notes.append("NOT NULL")
            if default and "nextval" not in str(default):
                notes.append(f"default: {default}")
            lines.append(f"| {col} | {dtype} | {', '.join(notes)} |")
        lines.append("")

    if relationships:
        lines.append("## Relationships")
        lines.extend(relationships)

    return "\n".join(lines)


_RULES = """
## Rules
- Return ONLY a valid SELECT query — no INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, or any other write operation
- Always include a LIMIT (max 50 rows) unless the query uses an aggregate (COUNT, SUM, AVG, etc.)
- Use JOINs when the question involves related tables
- Use clear column aliases for readability
- Return ONLY the raw SQL string, no markdown, no explanation, no code fences
"""

_HEADER = "You are a SQL query generator. Given a natural language question, generate a PostgreSQL query to answer it.\n\n## Database Schema\n\n"


def get_sql_agent_prompt(db_config: dict) -> str:
    """Build the SQL agent prompt with live schema, cached in Redis with TTL."""
    cached = redis_client.get(REDIS_KEY)
    if cached:
        return cached

    schema_md = _fetch_schema(db_config)
    prompt = _HEADER + schema_md + "\n" + _RULES
    redis_client.set(REDIS_KEY, prompt, ex=CACHE_TTL)
    return prompt
