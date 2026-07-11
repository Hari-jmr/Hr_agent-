#!/usr/bin/env python3
"""
Batch PDF Ingestion Script for HR Agent Bot
Processes all PDFs in a directory and stores them in pgvector.

Usage:
    python scripts/seed-embeddings.py --pdf-dir ./pdfs/ --db-url "postgresql://..."

Prerequisites:
    - PostgreSQL with pgvector extension installed
    - OPENROUTER_API_KEY environment variable set
    - Backend Python dependencies installed
"""

import os
import sys
import argparse
import asyncio
from datetime import datetime, timezone
from pathlib import Path

# Add backend to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# Load .env file BEFORE importing main/Config
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import (
    Config,
    Base,
    Document,
    Chunk,
    DocumentProcessor,
    llm_client,
    OpenRouterClient,
)
import numpy as np

config = Config()

# Verify API key is loaded
if not config.OPENROUTER_API_KEY:
    print("❌ OPENROUTER_API_KEY not found!")
    print("   Please create backend/.env and add: OPENROUTER_API_KEY=sk-or-v1-...")
    sys.exit(1)


def get_db_session(db_url: str):
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal(), engine


async def ingest_single_pdf(db, file_path: Path, doc_id_prefix: str = "doc") -> dict:
    """Ingest a single PDF file into the database."""
    filename = file_path.name
    doc_id = f"{doc_id_prefix}_{datetime.now(timezone.utc).timestamp()}_{filename.replace(' ', '_').replace('.', '_')}"
    
    # Check if already ingested
    existing = db.query(Document).filter(Document.filename == filename, Document.ingested == True).first()
    if existing:
        print(f"  ⚠️  Already ingested: {filename} (id={existing.id})")
        return {"status": "skipped", "document_id": existing.id, "filename": filename}
    
    # Create document record
    doc = Document(
        id=doc_id,
        filename=filename,
        file_path=str(file_path),
        ingested=False
    )
    db.add(doc)
    db.commit()
    
    try:
        processor = DocumentProcessor()
        
        # Parse PDF
        print(f"  📖 Parsing PDF: {filename}")
        pages_content = await processor.parse_pdf(str(file_path))
        
        total_chunks = 0
        for page_content, page_num in pages_content:
            chunks = processor.semantic_chunk(
                page_content,
                page_num,
                config.CHUNK_SIZE,
                config.CHUNK_OVERLAP
            )
            
            for chunk in chunks:
                chunk_id = f"{doc_id}_chunk_{total_chunks}"
                
                # Generate embedding
                embedding = await llm_client.get_embedding(chunk["content"])
                embedding_vec = np.array(embedding, dtype=np.float32)
                
                # Store chunk
                db_chunk = Chunk(
                    id=chunk_id,
                    document_id=doc_id,
                    content=chunk["content"],
                    page_number=chunk["page_number"],
                    chunk_index=chunk["chunk_index"],
                    embedding=embedding_vec
                )
                db.add(db_chunk)
                total_chunks += 1
                
                if total_chunks % 10 == 0:
                    print(f"  🧩 Embedded chunk #{total_chunks}...")
        
        # Update document
        doc.ingested = True
        doc.total_chunks = total_chunks
        db.commit()
        
        print(f"  ✅ Done: {total_chunks} chunks embedded")
        return {"status": "success", "document_id": doc_id, "filename": filename, "chunks": total_chunks}
    
    except Exception as e:
        print(f"  ❌ Error: {e}")
        db.rollback()
        db.delete(doc)
        db.commit()
        return {"status": "error", "filename": filename, "error": str(e)}


async def main():
    parser = argparse.ArgumentParser(description="Batch ingest PDFs into HR Agent Bot")
    parser.add_argument("--pdf-dir", type=str, default="./pdfs", help="Directory containing PDF files")
    parser.add_argument("--db-url", type=str, default=config.DATABASE_URL, help="PostgreSQL connection string")
    parser.add_argument("--init-db", action="store_true", help="Create database tables before ingestion")
    args = parser.parse_args()
    
    pdf_dir = Path(args.pdf_dir).resolve()
    if not pdf_dir.exists():
        print(f"❌ PDF directory not found: {pdf_dir}")
        sys.exit(1)
    
    # Get all PDFs
    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ No PDF files found in {pdf_dir}")
        sys.exit(1)
    
    print(f"📦 Found {len(pdf_files)} PDF(s) in {pdf_dir}")
    print(f"🔗 Database: {args.db_url}")
    print("")
    
    # Connect to DB
    db, engine = get_db_session(args.db_url)
    
    if args.init_db:
        print("🔧 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created\n")
    
    # Process each PDF
    results = []
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
        result = await ingest_single_pdf(db, pdf_file)
        results.append(result)
        print("")
    
    # Summary
    successful = [r for r in results if r["status"] == "success"]
    skipped = [r for r in results if r["status"] == "skipped"]
    errors = [r for r in results if r["status"] == "error"]
    
    print("═══════════════════════════════════════════")
    print("📊 INGESTION SUMMARY")
    print("═══════════════════════════════════════════")
    print(f"  ✅ Successful: {len(successful)} documents")
    print(f"  ⏭️  Skipped:     {len(skipped)} documents")
    print(f"  ❌ Errors:      {len(errors)} documents")
    if successful:
        total_chunks = sum(r.get("chunks", 0) for r in successful)
        print(f"  🧩 Total chunks embedded: {total_chunks}")
    print("")
    
    if errors:
        print("Failed files:")
        for e in errors:
            print(f"  - {e['filename']}: {e['error']}")
    
    db.close()
    print("🎉 All done!")


if __name__ == "__main__":
    asyncio.run(main())
