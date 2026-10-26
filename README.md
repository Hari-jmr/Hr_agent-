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
pdf2/        Active HR policy PDF corpus (not committed)
```

## Run locally on Windows

Use the existing PostgreSQL database from `backend/.env` and the OpenRouter key configured there. The backend now reads `backend/.env` before the root `.env` for local development.

From the repository root, start the backend in one PowerShell terminal:

```powershell
& ".\backend\.venv\Scripts\python.exe" -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001
```

In a second terminal, start the frontend:

```powershell
cd frontend
npm run dev
```

Open http://localhost:3000. Backend API docs are at http://localhost:8001/docs.

## Deploy with Docker

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

### Build/update the PDF2 index

```bash
docker cp pdf2/. hr_agent_backend:/project/pdf2/
docker exec hr_agent_backend python scripts/reingest.py --build-candidate
```

The script preflights `pdf2/` and writes the replacement into separate PDF2 tables. The application uses those PDF2 tables; the previous `documents`/`chunks` index is retained but not queried. **Do not drop the legacy tables until the candidate passes evaluation and the user confirms deletion.** `seed-embeddings.py` is a compatibility alias for this staged workflow; it no longer incrementally mixes PDFs into the legacy index.

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
