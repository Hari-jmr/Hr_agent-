from pathlib import Path

import pytest

from backend.services.indexing import (
    CorpusPreflightError,
    build_staged_index,
    prepare_pdf_directory,
)


class FakeProcessor:
    async def parse_pdf(self, path):
        if Path(path).name == "broken.pdf":
            raise ValueError("OCR is not installed")
        return [("Policy text", 1)]

    def semantic_chunk(self, content, page_number, chunk_size, chunk_overlap):
        return [
            {
                "content": content,
                "page_number": page_number,
                "chunk_index": 0,
            }
        ]


@pytest.mark.asyncio
async def test_preflight_is_sorted_and_only_accepts_pdf_files(tmp_path):
    (tmp_path / "B.PDF").write_bytes(b"pdf")
    (tmp_path / "a.pdf").write_bytes(b"pdf")
    (tmp_path / "notes.txt").write_text("not a pdf")

    prepared = await prepare_pdf_directory(tmp_path, FakeProcessor(), 512, 64)

    assert [doc.path.name for doc in prepared] == ["a.pdf", "B.PDF"]
    assert all(doc.chunks for doc in prepared)


@pytest.mark.asyncio
async def test_preflight_fails_as_a_whole_if_any_pdf_is_unreadable(tmp_path):
    (tmp_path / "good.pdf").write_bytes(b"pdf")
    (tmp_path / "broken.pdf").write_bytes(b"pdf")

    with pytest.raises(CorpusPreflightError, match="broken.pdf.*OCR is not installed"):
        await prepare_pdf_directory(tmp_path, FakeProcessor(), 512, 64)


@pytest.mark.asyncio
async def test_build_staged_index_batches_embeddings_and_writes_only_stage_models(
    tmp_path,
):
    (tmp_path / "handbook.pdf").write_bytes(b"candidate-pdf")
    queries = []

    class FakeModel:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class FakeSession:
        def __init__(self):
            self.deleted = []
            self.added = []
            self.closed = False

        class Transaction:
            def __init__(self, session):
                self.session = session

            def __enter__(self):
                return self.session

            def __exit__(self, _type, _value, _traceback):
                return False

        def begin(self):
            return self.Transaction(self)

        def query(self, model):
            session = self

            class DeleteQuery:
                def delete(self, synchronize_session=False):
                    session.deleted.append(model)

            return DeleteQuery()

        def add_all(self, objects):
            self.added.extend(objects)

        def flush(self):
            pass

        def close(self):
            self.closed = True

    session = FakeSession()

    async def embed_batch(texts):
        queries.extend(texts)
        return [[0.1] * 1536 for _ in texts]

    result = await build_staged_index(
        tmp_path,
        FakeProcessor(),
        embed_batch,
        lambda: session,
        FakeModel,
        FakeModel,
        512,
        64,
        "openai/text-embedding-3-small",
        batch_size=2,
    )

    assert result["documents"][0]["filename"] == "handbook.pdf"
    assert result["chunks"] == 1
    assert queries == ["Policy text"]
    assert len(session.deleted) == 2
    assert all(
        item.embedding and len(item.embedding) == 1536
        for item in session.added
        if hasattr(item, "embedding")
    )
    assert session.closed
