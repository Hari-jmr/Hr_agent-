# HR Agent Bot - Complete Architecture & Implementation Guide

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     NEXT.JS 18 FRONTEND                         │
│  (Chat UI, Document Ingestion, Admin Dashboard - SensAI Design) │
└────────────────────────┬────────────────────────────────────────┘
                         │ API Calls (HTTP/WebSocket)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FASTAPI + UV BACKEND                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Routes:                                                  │  │
│  │ • POST /api/ingest       - Upload & process PDFs       │  │
│  │ • POST /api/query        - Process user questions      │  │
│  │ • GET  /api/citations    - Fetch source documents      │  │
│  │ • GET  /api/documents    - List ingested documents     │  │
│  │ • DELETE /api/documents/{id} - Remove documents        │  │
│  │ • GET  /api/health      - System health check          │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
    ┌────────┐    ┌──────────────┐   ┌──────────────┐
    │OpenRouter   │PostgreSQL +   │   │Document Parser
    │API         │pgvector      │   │& Chunker
    │(LLM/Embed) │               │   │
    └────────┘    └──────────────┘   └──────────────┘
```

---

## 📊 Tech Stack Breakdown

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Next.js 18 + TypeScript + Tailwind v4 | Chat UI + admin dashboard |
| **Backend** | FastAPI + UV + Pydantic | API server + RAG pipeline |
| **Database** | PostgreSQL 15+ | Document storage + embeddings |
| **Vector DB** | pgvector extension | Semantic search |
| **LLM** | OpenRouter (Anthropic Claude) | Generate answers + streaming |
| **Embeddings** | OpenRouter (text-embedding) | Convert text → vectors |
| **Document Processing** | PyPDF2 + LangChain | Extract & chunk PDFs |
| **RAG** | LangChain + FAISS (in-memory) + pgvector | Retrieval & ranking |

---

## 🎨 Frontend Design System (SensAI)

- **Font**: Bricolage Grotesque
- **Colors**: Stone base + Purple accent (OKLCH)
- **UI Kit**: shadcn/ui (base-nova style)
- **Icons**: Hugeicons primary + Lucide secondary
- **Animations**: Framer Motion + Tailwind animations

---

## 📋 Project Structure

```
hr-agent-bot/
├── frontend/                       # Next.js 18 application
│   ├── app/
│   │   ├── layout.tsx             # Root layout + SensAI tokens
│   │   ├── page.tsx               # Main chat interface
│   │   ├── admin/
│   │   │   ├── layout.tsx         # Admin sidebar layout
│   │   │   ├── documents/page.tsx # Document management
│   │   │   └── settings/page.tsx  # Settings page
│   │   └── api/
│   │       └── chat/route.ts      # API wrapper (optional)
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatMessage.tsx    # Message component with citations
│   │   │   ├── ChatInput.tsx      # Input form
│   │   │   └── CitationTooltip.tsx# Citation reference
│   │   ├── admin/
│   │   │   ├── DocumentUpload.tsx # PDF upload dropzone
│   │   │   ├── DocumentTable.tsx  # Document list
│   │   │   └── IngestProgress.tsx # Progress indicator
│   │   └── ui/                    # shadcn/ui components
│   ├── lib/
│   │   ├── api.ts                 # API client (fetch wrapper)
│   │   ├── types.ts               # Shared TypeScript types
│   │   └── utils.ts               # Utility functions
│   ├── globals.css                # SensAI design tokens
│   ├── tailwind.config.ts         # Tailwind + OKLCH colors
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.ts
│
├── backend/                       # FastAPI application
│   ├── main.py                    # FastAPI app entry
│   ├── core/
│   │   ├── config.py              # Environment variables
│   │   ├── models.py              # Pydantic models
│   │   └── logging.py             # Logger setup
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py            # Chat endpoint
│   │   │   ├── documents.py       # Document CRUD
│   │   │   └── health.py          # Health check
│   │   └── dependencies.py        # FastAPI dependencies
│   ├── services/
│   │   ├── rag.py                 # RAG pipeline
│   │   ├── embeddings.py          # Embedding generation
│   │   ├── llm.py                 # OpenRouter LLM client
│   │   ├── document_processor.py  # PDF parsing & chunking
│   │   └── database.py            # DB operations
│   ├── db/
│   │   ├── models.py              # SQLAlchemy models
│   │   ├── schemas.py             # Database schemas
│   │   └── session.py             # DB connection
│   ├── utils/
│   │   ├── citations.py           # Citation formatting
│   │   └── chunk_formatter.py     # Chunk management
│   ├── tests/
│   │   ├── test_rag.py
│   │   ├── test_api.py
│   │   └── conftest.py
│   ├── requirements.txt           # Python dependencies
│   ├── pyproject.toml             # UV config
│   ├── .env.example
│   └── main.py
│
├── docker/
│   ├── Dockerfile.backend         # FastAPI container
│   ├── Dockerfile.frontend        # Next.js container
│   └── docker-compose.yml         # Local dev setup
│
├── scripts/
│   ├── init-db.sh                 # Init PostgreSQL + pgvector
│   └── seed-embeddings.py         # Batch ingest sample PDFs
│
└── README.md
```

---

## 🚀 Key Features

### 1. **Multi-turn Conversation with Memory**
- Conversation history stored in frontend state
- Context passed to backend for better answers
- Session-based tracking (optional: store in DB)

### 2. **Citation Support**
- Each answer includes source metadata:
  - Document name
  - Page number
  - Chunk reference
  - Confidence score
- Click citations → view original document section

### 3. **RAG Pipeline**
- **Chunking**: Semantic chunking (256-512 token overlaps)
- **Embedding**: OpenRouter text-embedding models
- **Storage**: pgvector for similarity search
- **Retrieval**: Hybrid search (BM25 + semantic)
- **Re-ranking**: LLM-based relevance scoring

### 4. **Admin Dashboard**
- Upload multiple PDFs (drag-drop)
- View ingestion status
- Delete documents
- View embedding stats

### 5. **Streaming Responses**
- Server-sent events (SSE) for real-time answer streaming
- Show citations incrementally

---

## 🔑 Environment Variables

### Backend (.env)
```
# OpenRouter
OPENROUTER_API_KEY=sk-or-v1-xxxxxxx
OPENROUTER_LLM_MODEL=anthropic/claude-3-5-sonnet
OPENROUTER_EMBED_MODEL=openai/text-embedding-3-small

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/hr_agent
POSTGRES_USER=admin
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=hr_agent

# Server
DEBUG=true
WORKERS=4
PORT=8000

# RAG
CHUNK_SIZE=512
CHUNK_OVERLAP=64
TOP_K_RETRIEVAL=5
SIMILARITY_THRESHOLD=0.7
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=HR Agent Bot
```

---

## 🔄 Data Flow Example

### User Query: "What is my notice period?"

```
1. Frontend (Chat UI)
   └─> User types question
   └─> Sends to /api/query with conversation history

2. Backend (RAG Pipeline)
   ├─> Embed question: "What is my notice period?"
   ├─> Search pgvector for similar chunks
   │   └─> Retrieve top-5 relevant document chunks
   ├─> Re-rank retrieved chunks
   │   └─> Filter by similarity_threshold (0.7)
   ├─> Format context with citations
   └─> Send to OpenRouter LLM:
       {
         "prompt": "Based on these HR policies: [CONTEXT], answer: [QUESTION]",
         "citations": [
           {
             "doc": "Leave_Policy.pdf",
             "page": 3,
             "chunk_id": "chunk_45",
             "text": "Notice period is 30 days..."
           }
         ]
       }

3. LLM (OpenRouter Claude)
   └─> Generate answer with citations
   └─> Stream response back to frontend

4. Frontend (Chat UI)
   ├─> Display answer incrementally
   ├─> Show citation badges
   └─> Allow expand/collapse of source content
```

---

## 🛠️ Implementation Phases

### Phase 1: Infrastructure Setup
- [x] PostgreSQL + pgvector setup
- [x] FastAPI scaffolding
- [x] Next.js project with SensAI design tokens
- [x] OpenRouter API integration

### Phase 2: Core RAG
- [x] Document ingestion pipeline
- [x] Embedding generation
- [x] pgvector storage & search
- [x] Citation tracking

### Phase 3: Chat & Frontend
- [x] Chat API endpoint
- [x] Streaming responses
- [x] Chat UI (SensAI design)
- [x] Citation UI components

### Phase 4: Admin Dashboard
- [ ] Document upload (dropzone)
- [ ] Ingestion progress tracking
- [ ] Document deletion
- [ ] Embedding stats dashboard

### Phase 5: Polish & Deploy
- [x] Error handling & logging
- [ ] Rate limiting
- [ ] Performance optimization
- [x] Docker containerization
- [ ] CI/CD pipeline

---

## 🧪 Testing Strategy

- **Unit Tests**: RAG pipeline, embeddings, citation formatting
- **Integration Tests**: API endpoints, database operations
- **E2E Tests**: Full chat flow with multiple questions
- **Performance Tests**: Query latency, embedding speed

---

## 📈 Performance Considerations

| Metric | Target | Implementation |
|--------|--------|-----------------|
| **First Query** | <3s | Pre-loaded embeddings |
| **Follow-up Query** | <1.5s | Cached connections |
| **Citation Accuracy** | >95% | Chunk-level tracking |
| **Embedding Cost** | ~$0.02 per 1M tokens | Batch ingestion |
| **Max Users** | 100+ concurrent | Connection pooling |

---

## 🔐 Security Checklist

- [x] CORS configured (frontend domain only)
- [ ] Rate limiting on endpoints
- [x] Input validation on all APIs
- [x] Secure .env handling (no secrets in code)
- [x] SQL injection prevention (SQLAlchemy ORM)
- [ ] HTTPS in production
- [ ] API authentication (JWT optional)

---

## 📚 Next Steps

1. **Read**: Backend setup (FastAPI + Database)
2. **Read**: Frontend setup (Next.js + Chat UI)
3. **Read**: RAG pipeline implementation
4. **Read**: Citation system design
5. **Deploy**: Docker compose for local testing
6. **Scale**: Kubernetes / cloud deployment
