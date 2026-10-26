import pytest

from backend import main


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def mappings(self):
        return self.rows


class FakeDatabase:
    def __init__(self):
        self.statements = []

    def execute(self, statement, params):
        sql = str(statement)
        self.statements.append((sql, params))
        if "ts_rank_cd" in sql:
            return FakeResult(
                [
                    {
                        "id": "chunk-vector",
                        "document_id": "doc-1",
                        "document_name": "Handbook.pdf",
                        "content": "Vector and keyword match",
                        "page_number": 4,
                        "chunk_index": 0,
                        "lexical_score": 0.5,
                    },
                    {
                        "id": "chunk-keyword",
                        "document_id": "doc-2",
                        "document_name": "Travel.pdf",
                        "content": "Exact policy amount",
                        "page_number": 8,
                        "chunk_index": 1,
                        "lexical_score": 0.25,
                    },
                ]
            )
        return FakeResult(
            [
                {
                    "id": "chunk-vector",
                    "document_id": "doc-1",
                    "document_name": "Handbook.pdf",
                    "content": "Vector and keyword match",
                    "page_number": 4,
                    "chunk_index": 0,
                    "distance": 0.2,
                }
            ]
        )


@pytest.mark.asyncio
async def test_retriever_merges_semantic_and_lexical_candidates(monkeypatch):
    async def fake_embedding(_query):
        return [0.0] * 1536

    monkeypatch.setattr(main.llm_client, "get_embedding", fake_embedding)
    db = FakeDatabase()
    service = main.RAGService(db)

    chunks = await service.retrieve_relevant_chunks("Saudi Arabia per diem", top_k=5)

    assert "chunks_pdf2_stage" in db.statements[0][0]
    assert "documents_pdf2_stage" in db.statements[0][0]
    assert {chunk["chunk_id"] for chunk in chunks} == {
        "chunk-vector",
        "chunk-keyword",
    }
    vector_chunk = next(
        chunk for chunk in chunks if chunk["chunk_id"] == "chunk-vector"
    )
    lexical_chunk = next(
        chunk for chunk in chunks if chunk["chunk_id"] == "chunk-keyword"
    )
    assert vector_chunk["retrieval_methods"] == {"semantic", "lexical"}
    assert vector_chunk["similarity_score"] == pytest.approx(0.8)
    assert lexical_chunk["retrieval_methods"] == {"lexical"}
    assert "Saudi Arabia per diem" in db.statements[1][1]["query"]
    assert all(
        ":query_embedding" in sql or "websearch_to_tsquery" in sql
        for sql, _ in db.statements
    )
