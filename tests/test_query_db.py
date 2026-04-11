from functions import query_db as query_db_module


def _response_with_content(content: str):
    return {"choices": [{"message": {"content": content}}]}


def test_validate_query_rejects_non_read_only_patterns():
    assert query_db_module._validate_query("SELECT 1; SELECT 2") == "Only a single SELECT statement is allowed."
    assert query_db_module._validate_query("SELECT 1 -- comment") == "SQL comments are not allowed."
    assert query_db_module._validate_query("DELETE FROM users") == "Only SELECT queries are allowed. Got: DELETE"


def test_validate_query_allows_select_and_cte_queries():
    assert query_db_module._validate_query("SELECT 1") is None
    assert query_db_module._validate_query("WITH recent AS (SELECT 1) SELECT * FROM recent") is None


def test_generate_sql_reads_structured_json(monkeypatch):
    monkeypatch.setattr(query_db_module, "get_sql_agent_prompt", lambda _: "prompt")
    monkeypatch.setattr(
        query_db_module.llm_client.chat.completions,
        "create",
        lambda **_: _response_with_content('{"sql":"SELECT * FROM orders LIMIT 5"}'),
    )

    sql = query_db_module._generate_sql("Show recent orders")

    assert sql == "SELECT * FROM orders LIMIT 5"


def test_generate_sql_returns_empty_on_malformed_json(monkeypatch):
    monkeypatch.setattr(query_db_module, "get_sql_agent_prompt", lambda _: "prompt")
    monkeypatch.setattr(
        query_db_module.llm_client.chat.completions,
        "create",
        lambda **_: _response_with_content("not json"),
    )

    sql = query_db_module._generate_sql("Show recent orders")

    assert sql == ""
