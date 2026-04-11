import uuid

import pytest

from database.models import ChatMessage, ChatSession


@pytest.mark.asyncio
async def test_export_returns_deterministic_markdown(async_client, session_factory, test_user):
    session_id = str(uuid.uuid4())

    async with session_factory() as session:
        session.add(
            ChatSession(
                id=session_id,
                user_id=test_user.id,
                title="Quarterly Review",
            )
        )
        session.add_all(
            [
                ChatMessage(
                    id=str(uuid.uuid4()),
                    chat_session_id=session_id,
                    role="user",
                    content="Summarize the quarter.",
                    tool_calls=[],
                    metadata_={},
                ),
                ChatMessage(
                    id=str(uuid.uuid4()),
                    chat_session_id=session_id,
                    role="assistant",
                    content="Revenue grew 12%.",
                    tool_calls=[{"id": "tool-1", "name": "query_db", "args": {"question": "quarter revenue"}}],
                    metadata_={
                        "parts": [
                            {
                                "type": "tool-call",
                                "toolCallId": "tool-1",
                                "toolName": "query_db",
                                "args": {"question": "quarter revenue"},
                                "argsText": '{"question": "quarter revenue"}',
                            }
                        ],
                        "sources": [
                            {"source": "Q4.pdf", "page": 3, "score": 0.91},
                        ],
                    },
                ),
            ]
        )
        await session.commit()

    response = await async_client.get(f"/chat/sessions/{session_id}/export")

    assert response.status_code == 200
    assert 'attachment; filename="quarterly-review.md"' == response.headers["content-disposition"]
    assert "# Quarterly Review" in response.text
    assert "## 1. User" in response.text
    assert "Summarize the quarter." in response.text
    assert "## 2. Assistant" in response.text
    assert "Revenue grew 12%." in response.text
    assert "### Tool Calls" in response.text
    assert "`query_db`" in response.text
    assert "### Sources" in response.text
    assert "`Q4.pdf` (page 3, score 0.91)" in response.text
