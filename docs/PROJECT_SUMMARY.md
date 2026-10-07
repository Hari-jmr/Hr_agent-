# 📦 HR Agent Bot - Project Summary & Implementation Guide

## ✨ Project Overview

**HR Agent Bot** is a production-ready conversational AI system for HR policy queries using:
- 🤖 **OpenRouter API** for LLM (Claude 3.5 Sonnet)
- 🗂️ **pgvector** for semantic vector search
- 💬 **FastAPI** backend with streaming responses
- 🎨 **Next.js 18** frontend with SensAI design system
- 📚 **RAG Pipeline** for cited, accurate answers

---

## 🎯 Key Features

✅ **Multi-turn conversations** with context preservation  
✅ **Citation system** with source documents and page references  
✅ **Streaming responses** for real-time UX  
✅ **Admin dashboard** for document management  
✅ **Semantic chunking** with intelligent overlap  
✅ **Hybrid retrieval** (BM25 + semantic similarity)  
✅ **SensAI design** - Bricolage Grotesque font, OKLCH colors, purple accent  
✅ **Production-ready** - Docker, logging, error handling  

---

## 📂 Complete File Structure

```
hr-agent-bot/
│
├── 📄 HR_AGENT_ARCHITECTURE.md          ← System design & tech stack
├── 📄 SETUP_GUIDE.md                    ← Complete setup instructions
├── 📄 PROJECT_SUMMARY.md                ← This file
│
├── 🔧 backend/
│   ├── main.py                          ← FastAPI app (OpenRouter + pgvector)
│   ├── requirements.txt                 ← Python dependencies
│   ├── pyproject.toml                   ← UV package manager config
│   ├── .env                             ← Environment variables (create this)
│   │
│   ├── core/
│   │   ├── config.py                    ← App configuration
│   │   ├── models.py                    ← Pydantic request/response models
│   │   └── logging.py                   ← Logging setup
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py                  ← Query endpoint
│   │   │   ├── documents.py             ← Document CRUD
│   │   │   └── health.py                ← Health check
│   │   └── dependencies.py              ← FastAPI dependencies
│   │
│   ├── services/
│   │   ├── rag.py                       ← RAG pipeline
│   │   ├── embeddings.py                ← OpenRouter embeddings
│   │   ├── llm.py                       ← OpenRouter LLM client
│   │   ├── document_processor.py        ← PDF parsing & chunking
│   │   └── database.py                  ← DB operations
│   │
│   ├── db/
│   │   ├── models.py                    ← SQLAlchemy models
│   │   ├── schemas.py                   ← Database schemas
│   │   └── session.py                   ← DB connection pool
│   │
│   └── tests/
│       ├── test_rag.py                  ← RAG pipeline tests
│       ├── test_api.py                  ← API endpoint tests
│       └── conftest.py                  ← Pytest configuration
│
├── 🎨 frontend/
│   ├── app/
│   │   ├── layout.tsx                   ← Root layout
│   │   ├── page.tsx                     ← Main chat interface
│   │   ├── globals.css                  ← SensAI design tokens
│   │   │
│   │   ├── admin/
│   │   │   ├── documents/
│   │   │   │   └── page.tsx             ← Document management
│   │   │   └── settings/
│   │   │       └── page.tsx             ← Admin settings
│   │   │
│   │   └── api/
│   │       └── chat/route.ts            ← Optional: API wrapper
│   │
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatMessage.tsx          ← Message with citations
│   │   │   ├── ChatInput.tsx            ← Input form
│   │   │   └── CitationTooltip.tsx      ← Citation reference
│   │   │
│   │   ├── admin/
│   │   │   ├── DocumentUpload.tsx       ← PDF dropzone
│   │   │   ├── DocumentTable.tsx        ← Document list
│   │   │   └── IngestProgress.tsx       ← Progress indicator
│   │   │
│   │   └── ui/                          ← shadcn/ui components
│   │       ├── button.tsx
│   │       ├── input.tsx
│   │       ├── card.tsx
│   │       ├── badge.tsx
│   │       ├── skeleton.tsx
│   │       └── ...
│   │
│   ├── lib/
│   │   ├── api.ts                       ← API client (fetch wrapper)
│   │   ├── types.ts                     ← Shared TypeScript types
│   │   └── utils.ts                     ← Utility functions (cn)
│   │
│   ├── tailwind.config.ts               ← Tailwind + OKLCH colors
│   ├── package.json                     ← Node dependencies
│   ├── tsconfig.json                    ← TypeScript config
│   ├── next.config.ts                   ← Next.js config
│   └── .env.local                       ← Frontend env vars (create this)
│
├── 🐳 docker/
│   ├── docker-compose.yml               ← Full local dev stack
│   ├── Dockerfile.backend               ← FastAPI container
│   └── Dockerfile.frontend              ← Next.js container
│
├── 🔨 scripts/
│   ├── init-db.sh                       ← PostgreSQL + pgvector setup
│   ├── seed-embeddings.py               ← Batch ingest PDFs
│   └── quickstart.sh                    ← One-command setup
│
└── 📚 docs/
    ├── API.md                           ← Complete API reference
    ├── RAG_PIPELINE.md                  ← RAG implementation details
    ├── CITATION_SYSTEM.md               ← Citation tracking & display
    └── DEPLOYMENT.md                    ← Production deployment guide
```

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites Check
```bash
docker --version          # ≥ 20.10
node --version           # ≥ 18.17
python3 --version        # ≥ 3.10
```

### 1. Get OpenRouter API Key
- Sign up free at: https://openrouter.ai
- Copy your API key: `sk-or-v1-...`

### 2. Run One-Command Setup
```bash
bash scripts/quickstart.sh
```

This will:
- ✅ Create `.env` with your API key
- ✅ Start PostgreSQL + pgvector
- ✅ Install backend dependencies
- ✅ Install frontend dependencies
- ✅ Start FastAPI backend
- ✅ Start Next.js frontend

### 3. Access Services
```
Frontend:   http://localhost:3000
API Docs:   http://localhost:8000/docs
PgAdmin:    http://localhost:5050
```

### 4. Test the System
1. Go to http://localhost:3000/admin/documents
2. Upload a sample HR PDF
3. Go to http://localhost:3000
4. Ask: "What is my notice period?"

---

## 🔑 Environment Variables

### Backend (.env)
```env
# OpenRouter LLM API
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_LLM_MODEL=anthropic/claude-3-5-sonnet
OPENROUTER_EMBED_MODEL=openai/text-embedding-3-small

# Database
DATABASE_URL=postgresql://admin:password@localhost:5432/hr_agent

# RAG Configuration
CHUNK_SIZE=512              # Document chunk size (tokens)
CHUNK_OVERLAP=64            # Overlap between chunks
TOP_K_RETRIEVAL=5           # How many chunks to retrieve
SIMILARITY_THRESHOLD=0.7    # Min similarity score

# Server
DEBUG=true
WORKERS=4
PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=HR Agent Bot
```

---

## 🏗️ Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│ User Query at http://localhost:3000                         │
└────────────────────┬────────────────────────────────────────┘
                     │ POST /api/query
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ FastAPI Backend (http://localhost:8000)                     │
├─────────────────────────────────────────────────────────────┤
│ 1. Embed question using OpenRouter embeddings              │
│ 2. Search pgvector for top-5 similar chunks                │
│ 3. Re-rank results by confidence                           │
│ 4. Format context with citations                           │
│ 5. Send to Claude 3.5 via OpenRouter                       │
│ 6. Stream response back with citations                     │
└────────────────────┬────────────────────────────────────────┘
                     │ Server-Sent Events (NDJSON)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Next.js Frontend (http://localhost:3000)                    │
├─────────────────────────────────────────────────────────────┤
│ 1. Display answer incrementally                             │
│ 2. Show citations with source badges                       │
│ 3. Allow expand/collapse of source previews               │
│ 4. Store in conversation history                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow: PDF Ingestion

```
Upload PDF at /admin/documents
        ↓
[Backend] Extract text using PyPDF2
        ↓
[Backend] Split into semantic chunks (512 tokens)
        ↓
[OpenRouter] Generate embeddings for each chunk
        ↓
[PostgreSQL + pgvector] Store chunks with vector embeddings
        ↓
Index created for fast similarity search
        ↓
Ready for retrieval!
```

---

## 🎯 Key Implementation Details

### 1. OpenRouter API Integration

```python
# backend/services/llm.py
class OpenRouterClient:
    async def stream_chat(self, messages: List[dict]):
        """Stream responses from Claude 3.5 Sonnet"""
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}"},
                json={
                    "model": "anthropic/claude-3-5-sonnet",
                    "messages": messages,
                    "stream": True,
                    "max_tokens": 1024
                }
            ) as response:
                async for chunk in response.aiter_text():
                    if chunk and chunk.startswith("data: "):
                        yield chunk[6:]
```

### 2. pgvector Similarity Search

```sql
-- Search for top-5 most similar chunks
SELECT 
    id, 
    document_id, 
    content,
    (embedding <-> query_embedding) as distance
FROM chunks
ORDER BY embedding <-> query_embedding
LIMIT 5;
```

### 3. Citation System

Each chunk stored with metadata:
```python
class Chunk(Base):
    id: str                  # chunk_12_345
    document_id: str         # doc_1
    content: str             # Chunk text
    page_number: int         # 3
    chunk_index: int         # 5
    embedding: vector(1536)  # pgvector
```

### 4. Streaming Responses

```typescript
// frontend/app/page.tsx
const response = await fetch('/api/query', {method: 'POST'});
const reader = response.body?.getReader();

while (true) {
    const {done, value} = await reader.read();
    if (done) break;
    
    const line = decoder.decode(value);
    const data = JSON.parse(line);
    
    if (data.type === 'chunk') {
        setMessage(msg => ({...msg, content: msg.content + data.content}));
    }
}
```

---

## 🧪 Testing

### Run Backend Tests
```bash
cd backend
pytest tests/ -v --cov=.
```

### Test API Endpoint
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is my notice period?",
    "session_id": "test-123"
  }'
```

### Test Frontend Build
```bash
cd frontend
npm run build
```

---

## 🔒 Security Best Practices

| Feature | Implementation |
|---------|----------------|
| **API Keys** | Stored in `.env`, never in git |
| **Database** | pgvector on private network |
| **CORS** | Restricted to allowed origins |
| **Input Validation** | Pydantic models for all inputs |
| **SQL Injection** | SQLAlchemy ORM prevents injection |
| **HTTPS** | Required in production |
| **Rate Limiting** | Configure on FastAPI routes |
| **Logging** | Structured logging, no PII |

---

## 📈 Performance Tips

1. **Database Indexing**
   ```sql
   CREATE INDEX chunks_embedding_idx ON chunks 
   USING ivfflat (embedding vector_cosine_ops);
   ```

2. **Connection Pooling**
   ```python
   engine = create_engine(
       DATABASE_URL,
       poolclass=QueuePool,
       pool_size=20,
       max_overflow=40
   )
   ```

3. **Frontend Optimization**
   - Code splitting with Next.js
   - Image optimization with next/image
   - Streaming responses instead of full loads

4. **Caching Strategy**
   - Redis for frequent queries
   - Browser cache for static assets
   - Database query results cache

---

## 🐛 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| **PostgreSQL connection fails** | Check `DATABASE_URL` in `.env`, ensure PostgreSQL running |
| **pgvector not found** | Run `init-db.sh` or create extension manually |
| **OpenRouter API errors** | Verify `OPENROUTER_API_KEY` with correct format |
| **CORS errors** | Update `CORS_ORIGINS` in backend `.env` |
| **Slow queries** | Create pgvector index, increase `pool_size` |
| **Memory issues** | Reduce `CHUNK_SIZE` or use pagination |

---

## 🚀 Production Deployment

### Option 1: Docker
```bash
docker build -t hr-agent-bot:latest .
docker run -p 8000:8000 \
  -e OPENROUTER_API_KEY=sk-or-v1-... \
  -e DATABASE_URL=postgresql://... \
  hr-agent-bot:latest
```

### Option 2: Vercel + Railway
```bash
# Frontend on Vercel
vercel deploy --prod

# Backend on Railway
railway up --service backend
```

### Option 3: AWS EC2 + RDS
```bash
# RDS PostgreSQL with pgvector
# EC2 instance with Docker
# CloudFront for CDN
# Application Load Balancer
```

---

## 📚 Documentation Links

- 📖 [Architecture Guide](./docs/HR_AGENT_ARCHITECTURE.md)
- 📖 [Setup Instructions](./docs/SETUP_GUIDE.md)
- 📖 [API Reference](./docs/API.md)
- 📖 [RAG Pipeline Details](./docs/RAG_PIPELINE.md)
- 📖 [Citation System](./docs/CITATION_SYSTEM.md)
- 📖 [Deployment Guide](./docs/DEPLOYMENT.md)

---

## 📞 Support & Contribution

- **Report Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: support@hragent.local

---

## 📄 License

MIT License - Free for personal and commercial use

---

## 🎓 Tech Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 18 + React 18 | Chat UI + admin dashboard |
| **Styling** | Tailwind CSS + shadcn/ui | SensAI design system |
| **Font** | Bricolage Grotesque | Brand typography |
| **Colors** | OKLCH (stone + purple) | Accessible color system |
| **Backend** | FastAPI + Uvicorn | High-performance API |
| **LLM** | OpenRouter (Claude 3.5) | Answer generation |
| **Embeddings** | OpenRouter (text-embedding-3) | Semantic search |
| **Database** | PostgreSQL 15 | Primary data store |
| **Vector DB** | pgvector | Semantic search index |
| **Document Processing** | PyPDF2 + LangChain | PDF parsing & chunking |
| **Container** | Docker + Docker Compose | Development & deployment |

---

**Version**: 1.0.0  
**Last Updated**: January 2024  
**Maintainer**: HR Agent Team  

🚀 Ready to deploy? Start with `bash scripts/quickstart.sh`!
