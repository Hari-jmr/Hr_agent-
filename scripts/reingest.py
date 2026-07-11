"""
Re-ingest all PDFs with cleaned text (strips headers/footers).
Run this from the project root directory.
"""
import sys
sys.path.insert(0, 'backend')

from dotenv import load_dotenv
load_dotenv()

import asyncio
import os
from datetime import datetime
from main import (
    SessionLocal, Document, Chunk, engine, Base,
    DocumentProcessor, llm_client, config, logger
)
import numpy as np

# PDF directory
PDF_DIR = "pdfs"

async def clear_and_reingest():
    db = SessionLocal()
    try:
        # Clear old data
        logger.info("Clearing old chunks and documents...")
        db.query(Chunk).delete()
        db.query(Document).delete()
        db.commit()
        logger.info("Old data cleared")
        
        pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]
        logger.info(f"Found {len(pdf_files)} PDFs to ingest")
        
        total_chunks = 0
        processor = DocumentProcessor()
        
        for pdf_file in pdf_files:
            file_path = os.path.join(PDF_DIR, pdf_file)
            doc_id = f"doc_{datetime.utcnow().timestamp()}_{pdf_file.replace(' ', '_').replace('.', '_')}"
            
            logger.info(f"Ingesting: {pdf_file}")
            
            # Parse PDF with cleaned text
            pages_content = await processor.parse_pdf(file_path)
            
            if not pages_content:
                logger.warning(f"No text extracted from {pdf_file}")
                continue
            
            # Create document record
            doc = Document(
                id=doc_id,
                filename=pdf_file,
                file_path=file_path,
                ingested=False
            )
            db.add(doc)
            
            doc_total_chunks = 0
            for page_content, page_num in pages_content:
                chunks = processor.semantic_chunk(
                    page_content,
                    page_num,
                    config.CHUNK_SIZE,
                    config.CHUNK_OVERLAP
                )
                
                for chunk in chunks:
                    chunk_id = f"{doc_id}_chunk_{doc_total_chunks}"
                    
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
                    doc_total_chunks += 1
                    total_chunks += 1
            
            # Update document
            doc.ingested = True
            doc.total_chunks = doc_total_chunks
            db.commit()
            
            logger.info(f"  -> {pdf_file}: {doc_total_chunks} chunks")
        
        logger.info(f"Re-ingestion complete! Total chunks: {total_chunks}")
        
    except Exception as e:
        logger.error(f"Re-ingestion error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(clear_and_reingest())
