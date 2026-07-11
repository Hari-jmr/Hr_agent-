import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import json
import os
import sys

# Ensure project root is on sys.path so "backend.*" imports work
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware

import httpx
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, Float, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pgvector.sqlalchemy import Vector
import numpy as np

from backend.api.router import api_router
from backend.core.config import config
from backend.schemas.common import ErrorDetail, ErrorResponse, StatusResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE SETUP
# ============================================================================

Base = declarative_base()

class Document(Base):
    """Document model"""
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    total_chunks = Column(Integer, default=0)
    embedding_model = Column(String, default="openai/text-embedding-3-small")
    created_at = Column(DateTime, default=datetime.utcnow)
    ingested = Column(Boolean, default=False)

class Chunk(Base):
    """Document chunk model"""
    __tablename__ = "chunks"

    id = Column(String, primary_key=True)
    document_id = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer)
    chunk_index = Column(Integer)
    embedding = Column(Vector(1536))
    created_at = Column(DateTime, default=datetime.utcnow)

class ConversationHistory(Base):
    """Store conversation context"""
    __tablename__ = "conversation_history"

    id = Column(String, primary_key=True)
    session_id = Column(String, nullable=False)
    role = Column(String)
    content = Column(Text, nullable=False)
    citations = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class Citation(BaseModel):
    """Citation metadata"""
    document_id: str = Field(..., description="Document ID")
    document_name: str = Field(..., description="Document filename")
    page_number: Optional[int] = Field(None, description="Page number")
    chunk_id: str = Field(..., description="Chunk reference ID")
    content_preview: str = Field(..., description="First 150 chars of chunk")
    confidence_score: float = Field(..., description="Similarity score 0-1")

class ChatMessage(BaseModel):
    """Chat message structure"""
    model_config = {"extra": "ignore"}
    role: str
    content: str
    citations: Optional[List[Citation]] = None
    timestamp: Optional[datetime] = None

class QueryRequest(BaseModel):
    """User query request"""
    model_config = {"extra": "ignore"}
    question: str = Field(..., min_length=5, max_length=1000)
    conversation_history: Optional[List[ChatMessage]] = None
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    """Query response with streaming"""
    answer: str
    citations: List[Citation]
    processing_time_ms: float
    model: str = config.OPENROUTER_LLM_MODEL

class DocumentInfo(BaseModel):
    """Document metadata"""
    id: str
    filename: str
    total_chunks: int
    created_at: datetime
    ingested: bool

class IngestionStatus(BaseModel):
    """Ingestion progress"""
    filename: str
    status: str
    progress_percent: int
    total_chunks: int
    error: Optional[str] = None

# ============================================================================
# OPENROUTER LLM CLIENT
# ============================================================================

class OpenRouterClient:
    """OpenRouter API client for LLM and embeddings"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"

    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenRouter"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": config.OPENROUTER_EMBED_MODEL,
                    "input": text
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]

    async def stream_chat(self, messages: List[dict], system_prompt: str):
        """Stream chat response from OpenRouter"""
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": config.OPENROUTER_LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        *messages
                    ],
                    "temperature": 0.7,
                    "stream": True,
                    "max_tokens": 1024
                },
                timeout=60.0
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data != "[DONE]":
                            try:
                                chunk = json.loads(data)
                                if "choices" in chunk and chunk["choices"]:
                                    delta = chunk["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                pass

llm_client = OpenRouterClient(config.OPENROUTER_API_KEY)

# ============================================================================
# RAG PIPELINE SERVICES
# ============================================================================

class DocumentProcessor:
    """PDF parsing and chunking using PyMuPDF"""

    HEADER_PATTERNS = [
        r'^Human Resources\s*$',
        r'^Document No\.\s*$',
        r'^L3/.*$',
        r'^JMR Infotech.*$',
        r'^Version No\.\s*$',
        r'^V\d+\.\d+\s*$',
        r'^Date\s*$',
        r'^\d+\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\s*$',
        r'^Version:\s*\d+\.\d+\s*$',
        r'^\u00a9\d{4}\s+JMR\s+Infotech.*$',
        r'All rights reserved',
        r'^Passing on and',
        r'^www\.jmrinfotech\.com',
        r'^Page \d+ of \d+',
        r'^\d+/\d+\s*$',
        r'^\d+\s*$',
        r'^\s*$',
    ]

    @staticmethod
    def clean_page_text(text: str) -> str:
        import re
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            stripped = line.strip()
            skip = False
            for pattern in DocumentProcessor.HEADER_PATTERNS:
                if re.match(pattern, stripped, re.IGNORECASE):
                    skip = True
                    break
            if not skip and len(stripped) <= 3 and stripped.isdigit():
                skip = True
            if not skip:
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines).strip()

    @staticmethod
    async def parse_pdf(file_path: str) -> List[tuple]:
        try:
            import fitz
            pages_content = []

            with fitz.open(file_path) as doc:
                for page_num, page in enumerate(doc, 1):
                    raw_text = page.get_text()
                    cleaned = DocumentProcessor.clean_page_text(raw_text)
                    if cleaned:
                        pages_content.append((cleaned, page_num))

            if not pages_content:
                logger.warning(f"No text extracted from {file_path}")
                return []

            logger.info(f"PyMuPDF extracted {len(pages_content)} pages from {file_path}")
            return pages_content
        except Exception as e:
            logger.error(f"PyMuPDF parsing error: {e}")
            raise

    @staticmethod
    def semantic_chunk(text: str, page_num: int, chunk_size: int = 512, overlap: int = 64) -> List[dict]:
        chunks = []
        words = text.split()

        if len(words) <= chunk_size:
            if text.strip():
                chunks.append({
                    "content": text.strip(),
                    "page_number": page_num,
                    "chunk_index": 0
                })
            return chunks

        step = chunk_size - overlap
        chunk_index = 0

        for i in range(0, len(words), step):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)

            if chunk_text.strip():
                chunks.append({
                    "content": chunk_text.strip(),
                    "page_number": page_num,
                    "chunk_index": chunk_index
                })
                chunk_index += 1

        return chunks

class RAGService:
    """Retrieval-Augmented Generation service"""

    def __init__(self, db: Session):
        self.db = db

    async def retrieve_relevant_chunks(self, query: str, top_k: int = 5) -> List[dict]:
        try:
            query_embedding = await llm_client.get_embedding(query)
            query_vec = np.array(query_embedding, dtype=np.float32)
            query_embedding_str = '[' + ','.join(str(x) for x in query_vec.tolist()) + ']'

            sql = text(f"""
                SELECT 
                    c.id,
                    c.document_id,
                    d.filename as document_name,
                    c.content,
                    c.page_number,
                    c.chunk_index,
                    c.embedding <=> '{query_embedding_str}'::vector as distance
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
                ORDER BY c.embedding <=> '{query_embedding_str}'::vector
                LIMIT :top_k
            """)

            result = self.db.execute(sql, {"top_k": top_k})

            relevant_chunks = []
            for row in result.mappings():
                distance = float(row["distance"])
                similarity = max(0.0, 1.0 - distance)

                if similarity >= config.SIMILARITY_THRESHOLD:
                    relevant_chunks.append({
                        "chunk_id": row["id"],
                        "document_id": row["document_id"],
                        "document_name": row["document_name"],
                        "content": row["content"],
                        "page_number": row["page_number"],
                        "chunk_index": row["chunk_index"],
                        "similarity_score": similarity
                    })

            logger.info(f"Retrieved {len(relevant_chunks)} chunks for query (threshold={config.SIMILARITY_THRESHOLD})")
            return relevant_chunks

        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            raise

    async def format_context_with_citations(self, chunks: List[dict], query: str) -> tuple:
        context_parts = []
        citations = []

        for i, chunk in enumerate(chunks):
            context_parts.append(f"[Source {i+1}] {chunk['content']}")

            citations.append(Citation(
                document_id=chunk.get("document_id", ""),
                document_name=chunk.get("document_name", "Unknown"),
                page_number=chunk.get("page_number"),
                chunk_id=chunk.get("chunk_id", ""),
                content_preview=chunk["content"][:150] + "...",
                confidence_score=chunk.get("similarity_score", 0.0)
            ))

        context = "\n\n".join(context_parts)
        return context, citations

    async def generate_answer_with_citations(self, query: str, context: str, citations: List[Citation]):
        system_prompt = f"""You are an HR Policy Assistant. Answer the user's specific question using ONLY the provided policy excerpts. Be direct and concise.

Rules:
1. ANSWER THE EXACT QUESTION ASKED — do not give a general overview of the whole policy
2. Use only the relevant excerpts that answer the question. Skip unrelated details.
3. Be specific: quote exact numbers, dates, durations, and procedures from the text.
4. If the answer is not in the excerpts, say "I couldn't find that in the current policies" and suggest what document to check.
5. Do NOT start with generic phrases like "According to the policy..." or "The document states that..." — jump straight to the facts.
6. Use bullet points or numbered steps ONLY if the answer has multiple distinct items.
7. Keep it brief. One or two sentences per point is enough.

Retrieved Policy Excerpts:
{context}"""

        messages = [{"role": "user", "content": query}]

        async def answer_generator():
            yield json.dumps({"type": "start", "citations": [c.dict() for c in citations]}).encode() + b"\n"

            async for chunk in llm_client.stream_chat(messages, system_prompt):
                yield json.dumps({"type": "chunk", "content": chunk}).encode() + b"\n"

            yield json.dumps({"type": "end"}).encode() + b"\n"

        return answer_generator()

# ============================================================================
# APP FACTORY
# ============================================================================

def _format_validation_loc(location: tuple[object, ...]) -> str | None:
    parts = [str(part) for part in location if part != 'body']
    return '.'.join(parts) if parts else None

def _build_validation_details(errors: list[dict]) -> list[ErrorDetail]:
    return [
        ErrorDetail(
            field=_format_validation_loc(error.get('loc', ())),
            message=error.get('msg', 'Invalid value'),
        )
        for error in errors
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('HR Agent API starting up')
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized")
    yield
    logger.info('HR Agent API shutting down')


def create_app() -> FastAPI:
    app = FastAPI(
        title=config.APP_NAME,
        version=config.APP_VERSION,
        docs_url='/docs',
        redoc_url='/redoc',
        lifespan=lifespan,
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=config.SECRET_KEY,
        same_site='lax',
        https_only=False,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=['GET', 'POST'],
        allow_headers=['*'],
    )

    # ------------------------------------------------------------------
    # Auth routes
    # ------------------------------------------------------------------
    app.include_router(api_router, prefix='/api')

    # ------------------------------------------------------------------
    # RAG endpoints
    # ------------------------------------------------------------------

    @app.get("/api/health")
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "llm_model": config.OPENROUTER_LLM_MODEL
        }

    @app.post("/api/query", response_class=StreamingResponse)
    async def query_handler(request: QueryRequest, background_tasks: BackgroundTasks):
        try:
            db = SessionLocal()
            rag_service = RAGService(db)

            relevant_chunks = await rag_service.retrieve_relevant_chunks(
                request.question,
                top_k=config.TOP_K_RETRIEVAL
            )

            context, citations = await rag_service.format_context_with_citations(
                relevant_chunks,
                request.question
            )

            answer_stream = await rag_service.generate_answer_with_citations(
                request.question,
                context,
                citations
            )

            return StreamingResponse(
                answer_stream,
                media_type="application/x-ndjson"
            )

        except Exception as e:
            logger.error(f"Query error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/documents/upload")
    async def upload_document(
        file: UploadFile = File(...),
        background_tasks: BackgroundTasks = None
    ):
        try:
            if not file.filename.endswith(".pdf"):
                raise HTTPException(status_code=400, detail="Only PDF files allowed")

            db = SessionLocal()
            doc_id = f"doc_{datetime.utcnow().timestamp()}"
            file_path = f"/tmp/{doc_id}_{file.filename}"

            contents = await file.read()
            with open(file_path, "wb") as f:
                f.write(contents)

            doc = Document(
                id=doc_id,
                filename=file.filename,
                file_path=file_path,
                ingested=False
            )
            db.add(doc)
            db.commit()

            if background_tasks:
                background_tasks.add_task(ingest_document, doc_id, file_path)

            return {
                "document_id": doc_id,
                "filename": file.filename,
                "status": "queued_for_ingestion"
            }

        except Exception as e:
            logger.error(f"Upload error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/documents")
    async def list_documents():
        db = SessionLocal()
        docs = db.query(Document).filter(Document.ingested == True).all()
        return [
            DocumentInfo(
                id=d.id,
                filename=d.filename,
                total_chunks=d.total_chunks,
                created_at=d.created_at,
                ingested=d.ingested
            )
            for d in docs
        ]

    @app.delete("/api/documents/{document_id}")
    async def delete_document(document_id: str):
        db = SessionLocal()
        doc = db.query(Document).filter(Document.id == document_id).first()

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        db.query(Chunk).filter(Chunk.document_id == document_id).delete()
        db.delete(doc)
        db.commit()

        return {"message": "Document deleted", "document_id": document_id}

    # ------------------------------------------------------------------
    # Error handlers
    # ------------------------------------------------------------------

    @app.exception_handler(HTTPException)
    async def handle_http_exception(_: Request, exc: HTTPException):
        message = exc.detail if isinstance(exc.detail, str) else 'Request failed.'
        details = _build_validation_details(exc.detail) if isinstance(exc.detail, list) else []
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(error=message, details=details).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(_: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error='Validation error.',
                details=_build_validation_details(exc.errors()),
            ).model_dump(),
        )

    @app.get('/health', response_model=StatusResponse)
    def healthcheck() -> StatusResponse:
        return StatusResponse(status='ok')

    return app


app = create_app()

# ------------------------------------------------------------------
# Background ingestion task
# ------------------------------------------------------------------

async def ingest_document(doc_id: str, file_path: str):
    db = SessionLocal()
    try:
        logger.info(f"Ingesting document: {doc_id}")

        processor = DocumentProcessor()

        pages_content = await processor.parse_pdf(file_path)

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

                embedding = await llm_client.get_embedding(chunk["content"])
                embedding_vec = np.array(embedding, dtype=np.float32)

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

        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.ingested = True
            doc.total_chunks = total_chunks
            db.commit()

        logger.info(f"Document ingested: {doc_id}, chunks: {total_chunks}")

    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        db.rollback()
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            db.delete(doc)
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=config.HOST,
        port=config.PORT,
        workers=int(os.getenv("WORKERS", 4))
    )
