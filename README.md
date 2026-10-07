# HR Agent Bot

Conversational assistant that answers HR policy questions with citations, streaming responses and multi-turn context.

```
Next.js UI  ->  /backend/*  (Next rewrite)  ->  FastAPI  ->  pgvector (policy chunks)
                                                  |              ^
                                                  v              |
                                             OpenRouter       HR policy PDFs
                                             (LLM + embeddings)
Employee login is verified against the existing Odoo PostgreSQL database.
```

## Stack

- **Frontend:** Next.js 15 (App Router), React 19, Tailwind CSS 4
- **Backend:** FastAPI, SQLAlchemy, pgvector (1536-dim embeddings)
- **LLM / embeddings:** OpenRouter (`openai/gpt-6-luna`, `openai/text-embedding-3-small`)
- **Auth:** Odoo 8.0 PostgreSQL (employee credentials + HR flag)
- **Database:** PostgreSQL 15 + pgvector

## Project structure

```
backend/     FastAPI app (main.py), api/ routes, core/ config, services/ (auth, db), schemas/
frontend/    Next.js app (app/, components/, lib/)
docker/      Dockerfile.backend, Dockerfile.frontend, docker-compose.yml
scripts/     init-db.sh, seed-embeddings.py, reingest.py, test-query.py
docs/        Architecture, API and deployment notes
pdfs/        HR policy PDFs to ingest (not committed)
```

## Deploy with Docker (recommended)

Prerequisites: Docker + Docker Compose on the server, an OpenRouter API key, network access to the Odoo PostgreSQL host, and the policy PDFs.

```bash
# 1. Clone
git clone https://github.com/Hari-jmr/Hr_agent-.git
cd Hr_agent-

# 2. Configure
cp .env.example .env
# edit .env: OPENROUTER_API_KEY, DB_HOST/DB_NAME/DB_USER/DB_PASSWORD (Odoo), SECRET_KEY

# 3. Build and start (postgres + backend + frontend)
docker compose -f docker/docker-compose.yml up -d --build
```

Access:

| Service  | URL                          |
| -------- | ---------------------------- |
| Frontend | http://SERVER_IP:3000        |
| API docs | http://SERVER_IP:8001/docs   |
| Health   | http://SERVER_IP:8001/api/health |

The database schema and the `vector` extension are created automatically on backend startup.

### Ingest the policy PDFs

```bash
docker cp pdfs/. hr_agent_backend:/project/pdfs/
docker exec hr_agent_backend python scripts/reingest.py
```

`reingest.py` clears and re-embeds every PDF in `pdfs/`. Use `seed-embeddings.py` to ingest without clearing (it skips files already ingested).

### Operations

```bash
docker compose -f docker/docker-compose.yml logs -f backend
docker compose -f docker/docker-compose.yml ps
docker compose -f docker/docker-compose.yml down            # stop
docker compose -f docker/docker-compose.yml up -d --build   # deploy updates (after git pull)
```

### Production checklist

- Put Nginx/Caddy in front of ports 3000/8001 for HTTPS; expose only 443 publicly (8001 is proxied by Next.js and does not need to be public).
- Set `DEBUG=false` and `ALLOWED_ORIGINS=https://your-domain` in `.env`.
- Backend container must reach the Odoo DB host/port (`DB_HOST`, `DB_PORT`).
- Keep `.env` out of git (already ignored) and rotate `OPENROUTER_API_KEY` / `SECRET_KEY` regularly.

## Local development (without Docker)

Backend:

```bash
cd backend
uv sync                           # creates .venv and installs all dependencies
uv run uvicorn main:app --reload --port 8001
```
`.env` is loaded from the repo root and `backend/` automatically.

Frontend:

```bash
cd frontend
npm install
npm run dev                       # http://localhost:3000
```

A local pgvector instance is required for the RAG database:

```bash
docker run --name hr_agent_pgvector -p 5433:5432 \
  -e POSTGRES_USER=admin -e POSTGRES_PASSWORD=secure_password -e POSTGRES_DB=hr_agent \
  -d pgvector/pgvector:pg15
```

## Environment variables

| Variable                                              | Used by   | Description                                    |
| ----------------------------------------------------- | --------- | ---------------------------------------------- |
| `OPENROUTER_API_KEY`                                  | backend   | OpenRouter key (LLM + embeddings)              |
| `OPENROUTER_LLM_MODEL`, `OPENROUTER_EMBED_MODEL`      | backend   | Model IDs                                      |
| `DATABASE_URL`                                        | backend   | pgvector connection string                     |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | backend | Odoo DB used for login                         |
| `SECRET_KEY`, `ALLOWED_ORIGINS`                       | backend   | Session signing, CORS                          |
| `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K_RETRIEVAL`, `SIMILARITY_THRESHOLD` | backend | RAG tuning |
| `NEXT_PUBLIC_BACKEND_URL`                             | frontend  | Target of the `/backend/*` rewrite             |

## License

MIT
