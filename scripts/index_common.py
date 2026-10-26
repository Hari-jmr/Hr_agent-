"""Build and validate a staged PDF2 index without touching the active corpus."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / "backend" / ".env")
load_dotenv(PROJECT_ROOT / ".env")

from backend.core.config import config
from backend.main import (
    DocumentProcessor,
    SessionLocal,
    StagedChunk,
    StagedDocument,
    engine,
    llm_client,
)
from backend.services.indexing import build_staged_index, prepare_pdf_directory


async def run_index_command(description: str) -> None:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--pdf-dir",
        type=Path,
        default=PROJECT_ROOT / "pdf2",
        help="PDF2 source directory (defaults to ./pdf2)",
    )
    parser.add_argument(
        "--build-candidate",
        action="store_true",
        help="Embed and atomically rebuild the PDF2 tables used by the app; leave legacy tables untouched",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Number of chunks sent in each embedding request",
    )
    args = parser.parse_args()
    if args.batch_size < 1 or args.batch_size > 128:
        parser.error("--batch-size must be between 1 and 128")

    processor = DocumentProcessor()
    prepared = await prepare_pdf_directory(
        args.pdf_dir,
        processor,
        config.CHUNK_SIZE,
        config.CHUNK_OVERLAP,
    )
    print(f"Preflight passed: {len(prepared)} PDFs from {args.pdf_dir.resolve()}")
    for document in prepared:
        print(
            f"  {document.path.name}: extracted_pages={len(document.pages)}, "
            f"chunks={len(document.chunks)}"
        )
    total_chunks = sum(len(document.chunks) for document in prepared)
    print(f"Total candidate chunks: {total_chunks}")

    if not args.build_candidate:
        print("Preflight only; active and staged indexes were not changed.")
        return

    if not config.OPENROUTER_API_KEY:
        parser.error("OPENROUTER_API_KEY is required to build embeddings")
    if not config.OPENROUTER_EMBED_MODEL:
        parser.error("OPENROUTER_EMBED_MODEL is required to build embeddings")

    target = urlparse(config.DATABASE_URL or "")
    print(
        "Building isolated candidate in database "
        f"host={target.hostname or 'unknown'} name={target.path.lstrip('/') or 'unknown'}"
    )
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
    StagedDocument.__table__.create(bind=engine, checkfirst=True)
    StagedChunk.__table__.create(bind=engine, checkfirst=True)

    try:
        result = await build_staged_index(
            args.pdf_dir,
            processor,
            llm_client.get_embeddings,
            SessionLocal,
            StagedDocument,
            StagedChunk,
            config.CHUNK_SIZE,
            config.CHUNK_OVERLAP,
            config.OPENROUTER_EMBED_MODEL,
            batch_size=args.batch_size,
            prepared_documents=prepared,
        )
    except Exception as exc:
        raise SystemExit(
            "Candidate embedding/build failed before commit; the previous staged "
            f"candidate and active index are unchanged: {exc}"
        ) from exc
    print(
        "PDF2 index built; legacy tables remain untouched: "
        f"documents={len(result['documents'])} chunks={result['chunks']} "
        f"embedding_model={result['embedding_model']}"
    )


def main(description: str) -> None:
    asyncio.run(run_index_command(description))
