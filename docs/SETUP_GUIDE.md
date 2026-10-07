# HR Agent Bot - Complete Setup & Deployment Guide

## 📋 Quick Start (Development)

### Prerequisites
- Python 3.10+ (for backend)
- Node.js 18+ (for frontend)
- PostgreSQL 15+ with pgvector extension
- OpenRouter API key (Free signup: https://openrouter.ai)

---

## 🚀 Backend Setup (FastAPI + pgvector)

### 1. Database Initialization

```bash
# Install PostgreSQL (macOS)
brew install postgresql@15
brew services start postgresql@15

# Install pgvector extension
psql postgres -c "CREATE DATABASE hr_agent_test;"
psql hr_agent_test -c "CREATE EXTENSION vector;"

# Or use Docker
docker run --name postgres_hr \
  -e POSTGRES_PASSWORD=secure_password \
  -e POSTGRES_DB=hr_agent \
  -p 5432:5432 \
  -d pgvector/pgvector:pg15

# Run initialization script
bash scripts/init-db.sh
```

### 2. Install Python Dependencies

```bash
cd backend

# Using UV (recommended)
uv venv
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows

uv pip install -r requirements.txt

# OR using pip
pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file:

```bash
# .env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxx
OPENROUTER_LLM_MODEL=anthropic/claude-3-5-sonnet
OPENROUTER_EMBED_MODEL=openai/text-embedding-3-small

DATABASE_URL=postgresql://admin:secure_password@localhost:5432/hr_agent

CHUNK_SIZE=512
CHUNK_OVERLAP=64
TOP_K_RETRIEVAL=5
SIMILARITY_THRESHOLD=0.7

DEBUG=true
WORKERS=4
PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### 4. Run Backend Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or with more workers
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

✅ Backend running at: http://localhost:8000
📚 API docs at: http://localhost:8000/docs

---

## 🎨 Frontend Setup (Next.js 18 + SensAI Design)

### 1. Install Dependencies

```bash
cd frontend

npm install
# or
yarn install
# or
pnpm install
```

### 2. Configure Environment

Create `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=HR Agent Bot
```

### 3. Run Development Server

```bash
npm run dev
# or
yarn dev
```

✅ Frontend running at: http://localhost:3000

### 4. Build for Production

```bash
npm run build
npm start
```

---

## 📄 Document Ingestion (Import HR Policies)

### Option 1: Upload via Admin Dashboard
1. Navigate to http://localhost:3000/admin/documents
2. Drag & drop PDF files
3. System automatically chunks, embeds, and indexes documents

### Option 2: Batch Ingest via Script

```bash
python scripts/seed-embeddings.py \
  --pdf-dir ./sample_policies/ \
  --db-url "postgresql://admin:password@localhost:5432/hr_agent"
```

### What Happens During Ingestion

```
PDF Upload
    ↓
Extract Text & Pages
    ↓
Semantic Chunking (512 tokens, 64 overlap)
    ↓
Generate Embeddings (OpenRouter)
    ↓
Store in pgvector + Metadata
    ↓
Ready for Retrieval!
```

---

## 🧪 Test the System

### Test Query via cURL

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is my notice period?",
    "session_id": "test-session-123"
  }'
```

### Test via Frontend

1. Open http://localhost:3000
2. Ask: "What is my notice period?"
3. System returns answer with citations
4. Click citations to view source documents

---

## 🐳 Docker Deployment

### Build Images

```bash
docker build -f docker/Dockerfile.backend -t hr-agent-bot:backend .
docker build -f docker/Dockerfile.frontend -t hr-agent-bot:frontend .
```

### Run with Docker Compose

```bash
docker-compose -f docker/docker-compose.yml up -d
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## ☁️ Production Deployment

### Option 1: AWS (EC2 + RDS)

```bash
# 1. Create RDS PostgreSQL instance with pgvector
# 2. Deploy backend to EC2
# 3. Deploy frontend to CloudFront + S3
# 4. Use Secrets Manager for API keys

aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name my-key \
  --security-groups default
```

### Option 2: Vercel + Railway

```bash
# Frontend on Vercel
vercel deploy --prod

# Backend on Railway
railway up --service backend
```

### Option 3: Kubernetes

```bash
kubectl apply -f k8s/postgres-pgvector.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

kubectl port-forward svc/backend 8000:8000
kubectl port-forward svc/frontend 3000:3000
```

---

## 🔍 API Documentation

### POST /api/query

**Request:**
```json
{
  "question": "What is my notice period?",
  "conversation_history": [
    {
      "role": "user",
      "content": "Hi, can you help?"
    },
    {
      "role": "assistant",
      "content": "Of course! What would you like to know?"
    }
  ],
  "session_id": "session-123"
}
```

**Response (Streaming NDJSON):**
```
{"type":"start","citations":[{"document_id":"doc_1","document_name":"Leave_Policy.pdf","page_number":3,"chunk_id":"chunk_45","content_preview":"Notice period is 30 days...","confidence_score":0.94}]}
{"type":"chunk","content":"The notice period at our company is "}
{"type":"chunk","content":"30 days"}
{"type":"chunk","content":" as per the employment agreement."}
{"type":"end"}
```

### GET /api/documents

**Response:**
```json
[
  {
    "id": "doc_1",
    "filename": "Leave_Policy.pdf",
    "total_chunks": 45,
    "created_at": "2024-01-15T10:30:00",
    "ingested": true
  }
]
```

### POST /api/documents/upload

**Request:** Multipart form-data with PDF file

**Response:**
```json
{
  "document_id": "doc_1704882600",
  "filename": "Leave_Policy.pdf",
  "status": "queued_for_ingestion"
}
```

### DELETE /api/documents/{document_id}

**Response:**
```json
{
  "message": "Document deleted",
  "document_id": "doc_1"
}
```

---

## 🔧 Troubleshooting

### Issue: "Connection refused" to PostgreSQL

**Solution:**
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Start PostgreSQL
brew services start postgresql@15
# or
docker-compose up -d postgres
```

### Issue: pgvector extension not found

**Solution:**
```bash
# Install pgvector in PostgreSQL
psql postgresql://user:password@localhost/hr_agent -c "CREATE EXTENSION vector;"

# Or with Docker image
docker pull pgvector/pgvector:pg15
```

### Issue: OpenRouter API key errors

**Solution:**
1. Get API key from https://openrouter.ai
2. Set in `.env`: `OPENROUTER_API_KEY=sk-or-v1-...`
3. Test with: `curl -H "Authorization: Bearer $OPENROUTER_API_KEY" https://openrouter.ai/api/v1/models`

### Issue: CORS errors between frontend and backend

**Solution:**
Update `CORS_ORIGINS` in backend `.env`:
```
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### Issue: Slow queries / high latency

**Solution:**
```sql
-- Create index on embeddings for faster similarity search
CREATE INDEX chunks_embedding_idx ON chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Check query performance
EXPLAIN ANALYZE 
SELECT * FROM chunks 
ORDER BY embedding <-> '[0.1, 0.2, ...]' 
LIMIT 5;
```

---

## 📊 Monitoring & Logging

### Backend Logs

```bash
# Watch logs
tail -f logs/backend.log

# Filter by level
grep "ERROR" logs/backend.log
```

### Database Monitoring

```bash
# Check table sizes
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Monitor connections
SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;

# Check embedding index health
SELECT * FROM pg_stat_user_indexes WHERE relname = 'chunks_embedding_idx';
```

### Frontend Performance

```bash
# Build analysis
npm run build -- --analyze

# Lighthouse audit
npm install -g lighthouse
lighthouse http://localhost:3000
```

---

## 🛡️ Security Checklist

- [ ] Environment variables not committed to git
- [ ] HTTPS enabled in production
- [ ] CORS configured for allowed origins only
- [ ] Rate limiting enabled on API endpoints
- [ ] Input validation on all user inputs
- [ ] SQL injection protection (SQLAlchemy ORM)
- [ ] API authentication (JWT optional)
- [ ] Database backups scheduled
- [ ] PII not logged or cached
- [ ] API keys rotated regularly

---

## 📈 Performance Optimization

### Database

```sql
-- Batch embed multiple documents
INSERT INTO chunks (id, document_id, content, embedding)
SELECT uuid_generate_v4(), doc_id, chunk_text, embedding
FROM temp_chunk_staging;

-- Vacuum to optimize space
VACUUM ANALYZE chunks;

-- Check stats
SELECT n_live_tup, n_dead_tup FROM pg_stat_user_tables 
WHERE relname = 'chunks';
```

### Backend

```python
# Enable caching
from fastapi_cache2 import FastAPICache2
from fastapi_cache2.backends.redis import RedisBackend

# Connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40
)
```

### Frontend

```bash
# Code splitting
npm run build

# Image optimization
next/image for lazy loading

# Streaming responses for better UX
ReadableStream instead of full response
```

---

## 📚 Additional Resources

- [OpenRouter API Docs](https://openrouter.ai/docs)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [LangChain + RAG Guide](https://python.langchain.com/docs/use_cases/qa_structured_sources/)
- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/deployment/)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Submit pull request

---

## 📞 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: support@hragent.local

---

## 📄 License

MIT License - See LICENSE file for details

---

**Last Updated**: January 2024
**Version**: 1.0.0
**Maintained by**: HR Agent Team
