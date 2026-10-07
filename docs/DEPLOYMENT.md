# Deployment Guide

The supported way to run this project is Docker Compose: PostgreSQL + pgvector, the FastAPI backend and the Next.js frontend.

## 1. Prepare the server

- Docker Engine 24+ with the Compose plugin (`docker compose version`)
- Outbound access to `https://openrouter.ai`
- Network access from the server to the Odoo PostgreSQL database (used for employee login)
- Ports: `3000` (frontend), `8001` (backend). Put a reverse proxy in front for HTTPS.

## 2. Configure environment

```bash
cp .env.example .env
```

Fill in `.env`:

| Variable | Required | Notes |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | yes | LLM + embeddings |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | yes | Odoo DB for login |
| `SECRET_KEY` | yes | long random string (session cookies) |
| `ALLOWED_ORIGINS` | yes | e.g. `https://hr.your-domain.com` |
| `DATABASE_URL` | no | overridden automatically inside compose |
| `OPENROUTER_LLM_MODEL`, `OPENROUTER_EMBED_MODEL` | no | default `openai/gpt-4o-mini`, `openai/text-embedding-3-small` |
| `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K_RETRIEVAL`, `SIMILARITY_THRESHOLD` | no | RAG tuning |

## 3. Start the stack

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

This starts:

| Container | Image / build | Port |
| --- | --- | --- |
| `hr_agent_postgres` | `pgvector/pgvector:pg15` | 5433 → 5432 |
| `hr_agent_backend` | `docker/Dockerfile.backend` | 8001 |
| `hr_agent_frontend` | `docker/Dockerfile.frontend` | 3000 |

Schema (`documents`, `chunks`, `conversation_history`) and the `vector` extension are created by the backend on startup (`backend/main.py` lifespan).

## 4. Ingest policy PDFs

```bash
docker cp pdfs/. hr_agent_backend:/project/pdfs/
docker exec hr_agent_backend python scripts/reingest.py       # clears + re-embeds all PDFs
# or, incremental (skips already ingested files):
docker exec hr_agent_backend python scripts/seed-embeddings.py --pdf-dir /project/pdfs
```

Embeddings are generated through OpenRouter, so ingestion requires a valid `OPENROUTER_API_KEY`.

## 5. Verify

```bash
curl http://localhost:8001/api/health
curl -X POST http://localhost:8001/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the notice period?", "session_id": "test-1"}'
```

Open http://SERVER_IP:3000 and log in with an Odoo employee account.

## 6. Updating

```bash
git pull
docker compose -f docker/docker-compose.yml up -d --build
```

## Reverse proxy (HTTPS)

Terminate TLS at Nginx/Caddy and proxy to the frontend container. Next.js already proxies `/backend/*` calls to the backend container, so only the frontend port must be exposed publicly.

Example Nginx server block:

```nginx
server {
    listen 443 ssl;
    server_name hr.your-domain.com;

    ssl_certificate     /etc/letsencrypt/live/hr.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/hr.your-domain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;   # required for streaming answers
    }
}
```

When using a domain, update `ALLOWED_ORIGINS` in `.env` and restart the backend.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `Login fails` | Backend container cannot reach Odoo: check `DB_HOST`/`DB_PORT` and network/firewall |
| `vector type not found` | pgvector extension missing; restart backend (it creates it) or run `docker exec hr_agent_postgres psql -U admin -d hr_agent -c 'CREATE EXTENSION vector;'` |
| `No answers / empty citations` | PDFs not ingested: run step 4 |
| `Query fails with 401/402` | Invalid or unfunded `OPENROUTER_API_KEY` |
| `CORS error in browser` | Add the exact frontend origin to `ALLOWED_ORIGINS` |
| `Docker build fails on frontend` | Ensure `frontend/public/` exists (contains `.gitkeep` in the repo) |
