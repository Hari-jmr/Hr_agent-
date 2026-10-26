import json
from datetime import datetime

import httpx
import pytest

from backend import main
from backend.services.intent_router import CHAT, RETRIEVE


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "reply",
    [
        "Hello! How can I help?",
        "I can help with JMR HR questions.",
        "Which part of the policy do you mean?",
    ],
)
async def test_chat_replies_never_open_db_or_retrieve(monkeypatch, reply):
    async def classify(_payload):
        return json.dumps({"intent": CHAT, "reply": reply})

    def unexpected_db_session():
        pytest.fail("CHAT must not open a database session")

    monkeypatch.setattr(main.llm_client, "classify_intent", classify)
    monkeypatch.setattr(main, "SessionLocal", unexpected_db_session)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=main.app), base_url="http://test"
    ) as client:
        response = await client.post("/api/query", json={"question": "hello"})

    assert response.status_code == 200
    events = [json.loads(line) for line in response.text.splitlines()]
    assert any(event.get("content") == reply for event in events)


@pytest.mark.asyncio
async def test_retrieve_decision_opens_db_and_runs_rag(monkeypatch):
    calls = {"db": 0, "queries": []}

    async def classify(_payload):
        return json.dumps(
            {
                "intent": RETRIEVE,
                "reply": "",
                "search_queries": [
                    "probation leave allowance",
                    "probation confirmation",
                ],
            }
        )

    class FakeRAGService:
        def __init__(self, _db):
            pass

        async def condense_query(self, question, _history):
            return question

        async def retrieve_relevant_chunks(self, _query, top_k):
            calls["queries"].append(_query)
            assert top_k == main.config.TOP_K_RETRIEVAL
            return []

        async def format_context_with_citations(self, chunks, _query):
            assert chunks == []
            return "", []

        async def generate_answer_with_citations(
            self, _query, _context, _citations, history=None
        ):
            pytest.fail("Empty retrieval evidence must bypass answer generation")

    def open_db():
        calls["db"] += 1

        class FakeSession:
            def close(self):
                pass

        return FakeSession()

    monkeypatch.setattr(main.llm_client, "classify_intent", classify)
    monkeypatch.setattr(main, "SessionLocal", open_db)
    monkeypatch.setattr(main, "RAGService", FakeRAGService)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=main.app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/query", json={"question": "How many annual leave days?"}
        )

    assert response.status_code == 200
    assert calls == {
        "db": 1,
        "queries": ["probation leave allowance", "probation confirmation"],
    }
    events = [json.loads(line) for line in response.text.splitlines()]
    assert any("couldn't find support" in event.get("content", "") for event in events)


@pytest.mark.asyncio
async def test_document_management_is_pdf2_only_and_read_only(monkeypatch):
    class FakeQuery:
        def filter(self, _condition):
            return self

        def all(self):
            return [
                main.StagedDocument(
                    id="pdf2-doc",
                    filename="JMR_Employee_Handbook.pdf",
                    file_path="pdf2/JMR_Employee_Handbook.pdf",
                    total_chunks=111,
                    created_at=datetime.now(),
                    ingested=True,
                )
            ]

    class FakeSession:
        def query(self, model):
            assert model is main.StagedDocument
            return FakeQuery()

        def close(self):
            pass

    monkeypatch.setattr(main, "SessionLocal", FakeSession)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=main.app), base_url="http://test"
    ) as client:
        listing = await client.get("/api/documents")
        upload = await client.post("/api/documents/upload")
        delete = await client.delete("/api/documents/pdf2-doc")

    assert listing.status_code == 200
    assert [item["filename"] for item in listing.json()] == [
        "JMR_Employee_Handbook.pdf"
    ]
    assert upload.status_code == 409
    assert delete.status_code == 409


@pytest.mark.asyncio
async def test_document_management_is_pdf2_only_and_read_only(monkeypatch):
    class FakeQuery:
        def filter(self, _condition):
            return self

        def all(self):
            return [
                main.StagedDocument(
                    id="pdf2-doc",
                    filename="JMR_Employee_Handbook.pdf",
                    file_path="pdf2/JMR_Employee_Handbook.pdf",
                    total_chunks=111,
                    created_at=datetime.now(),
                    ingested=True,
                )
            ]

    class FakeSession:
        def query(self, model):
            assert model is main.StagedDocument
            return FakeQuery()

        def close(self):
            pass

    monkeypatch.setattr(main, "SessionLocal", FakeSession)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=main.app), base_url="http://test"
    ) as client:
        listing = await client.get("/api/documents")
        upload = await client.post("/api/documents/upload")
        delete = await client.delete("/api/documents/pdf2-doc")

    assert listing.status_code == 200
    assert [item["filename"] for item in listing.json()] == [
        "JMR_Employee_Handbook.pdf"
    ]
    assert upload.status_code == 409
    assert delete.status_code == 409
