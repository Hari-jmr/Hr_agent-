"""Preflight helpers for building a replacement PDF corpus."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
from pathlib import Path
from typing import Any


class CorpusPreflightError(RuntimeError):
    """Raised when any candidate PDF cannot be fully prepared for indexing."""


@dataclass
class PreparedDocument:
    path: Path
    pages: list[tuple[str, int]]
    chunks: list[dict[str, Any]]


async def prepare_pdf_directory(
    pdf_dir: str | Path,
    processor: Any,
    chunk_size: int,
    chunk_overlap: int,
) -> list[PreparedDocument]:
    """Parse and chunk every PDF before callers mutate any index tables."""
    directory = Path(pdf_dir).expanduser().resolve()
    if not directory.is_dir():
        raise CorpusPreflightError(f"PDF directory does not exist: {directory}")

    pdf_files = sorted(
        (
            path
            for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() == ".pdf"
        ),
        key=lambda path: path.name.casefold(),
    )
    if not pdf_files:
        raise CorpusPreflightError(f"No PDF files found in {directory}")

    prepared: list[PreparedDocument] = []
    errors: list[str] = []
    for path in pdf_files:
        try:
            pages = await processor.parse_pdf(str(path))
            if not pages:
                raise ValueError("no usable text extracted")
            chunks = [
                chunk
                for content, page_number in pages
                for chunk in processor.semantic_chunk(
                    content,
                    page_number,
                    chunk_size,
                    chunk_overlap,
                )
            ]
            if not chunks:
                raise ValueError("no chunks produced")
            prepared.append(PreparedDocument(path=path, pages=pages, chunks=chunks))
        except Exception as exc:
            errors.append(f"{path.name}: {exc}")

    if errors:
        raise CorpusPreflightError(
            "PDF preflight failed; no candidate index was changed:\n- "
            + "\n- ".join(errors)
        )
    return prepared


async def build_staged_index(
    pdf_dir: str | Path,
    processor: Any,
    embed_batch: Any,
    session_factory: Any,
    document_model: Any,
    chunk_model: Any,
    chunk_size: int,
    chunk_overlap: int,
    embedding_model: str,
    batch_size: int = 64,
    prepared_documents: list[PreparedDocument] | None = None,
) -> dict[str, Any]:
    """Build/replace the isolated candidate corpus; never touch active tables."""
    prepared = prepared_documents or await prepare_pdf_directory(
        pdf_dir, processor, chunk_size, chunk_overlap
    )

    documents: list[dict[str, Any]] = []
    flat_chunks: list[tuple[int, dict[str, Any]]] = []
    for doc_number, item in enumerate(prepared):
        digest = sha256(item.path.read_bytes()).hexdigest()
        doc_id = f"pdf2_{sha256((item.path.name + digest).encode()).hexdigest()[:32]}"
        documents.append(
            {
                "id": doc_id,
                "filename": item.path.name,
                "file_path": str(item.path),
                "total_chunks": len(item.chunks),
                "embedding_model": embedding_model,
                "ingested": True,
                "extracted_text_pages": len(item.pages),
            }
        )
        flat_chunks.extend((doc_number, chunk) for chunk in item.chunks)

    vectors: list[list[float]] = []
    contents = [chunk["content"] for _, chunk in flat_chunks]
    for start in range(0, len(contents), batch_size):
        batch = await embed_batch(contents[start : start + batch_size])
        if len(batch) != len(contents[start : start + batch_size]):
            raise RuntimeError("Embedding batch size did not match requested inputs")
        for vector in batch:
            if len(vector) != 1536 or not all(
                math.isfinite(float(value)) for value in vector
            ):
                raise RuntimeError(
                    "Embedding response has invalid values or dimensions"
                )
        vectors.extend(batch)

    if len(vectors) != len(flat_chunks):
        raise RuntimeError("Embedding count does not match staged chunk count")

    db = session_factory()
    try:
        with db.begin():
            db.query(chunk_model).delete(synchronize_session=False)
            db.query(document_model).delete(synchronize_session=False)
            db.add_all(
                [
                    document_model(
                        **{
                            key: value
                            for key, value in item.items()
                            if key != "extracted_text_pages"
                        }
                    )
                    for item in documents
                ]
            )
            db.flush()

            staged_chunks = []
            doc_ids = [document["id"] for document in documents]
            for global_index, ((doc_number, chunk), vector) in enumerate(
                zip(flat_chunks, vectors)
            ):
                staged_chunks.append(
                    chunk_model(
                        id=f"{doc_ids[doc_number]}_chunk_{global_index}",
                        document_id=doc_ids[doc_number],
                        content=chunk["content"],
                        page_number=chunk["page_number"],
                        chunk_index=chunk["chunk_index"],
                        embedding=vector,
                    )
                )
            db.add_all(staged_chunks)

        return {
            "documents": documents,
            "chunks": len(flat_chunks),
            "embedding_model": embedding_model,
        }
    finally:
        db.close()
