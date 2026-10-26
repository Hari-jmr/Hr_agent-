# Progress — PDF2 Grounded HR Chatbot

**Status:** The application now uses the PDF2 index (15 documents / 280 chunks). The old index remains stored but is not used; delete it only after evaluation and explicit confirmation.
**Last updated:** 2026-10-26

## Goal

Replace the current indexed HR PDF corpus with the PDFs in `pdf2/` and improve the chatbot so it can answer indirect and situation-based questions from policy evidence, while clearly acknowledging missing, incomplete, or conflicting evidence.

## Work completed

- Inspected the current backend RAG flow, configuration, intent router, ingestion scripts, deployment guidance, and existing question sets.
- Audited the greeting/chat/policy route and recorded when DB, embedding, and vector retrieval are skipped versus invoked.
- Removed phrase-list greeting classification and replaced it with an OpenRouter intent classifier using two actions: `CHAT` (natural response, including greeting, redirection, or clarification) and `RETRIEVE` (policy lookup). The application validates labels; invalid classifier output falls back to retrieval.
- Recorded the current ingestion and answer-generation risks in `plan.md`.
- Extracted and reviewed both supplied DOCX question sets (about 110 questions) and inspected PDF2 extraction coverage and key Travel, Per Diem, referral, handbook, and ESK/PIL pages.
- Recorded the RAG architecture findings and recommendations in `plan.md`.
- Initialized the supplied `backend/.venv` development dependencies from the locked project config. Current suite: all 27 backend tests pass.
- Read-only database check: configured local `hr_agent` has 14 documents and 242 chunks; there is no vector ANN index (only the chunk primary-key index).
- Added RapidOCR as a local fallback for image-heavy PDF pages. PDF2 preflight now extracts all 15 PDFs and builds 280 candidate chunks, including the screenshot content in the Travel PDF.
- OpenRouter account check: account credit total is $300 with about $35.01 remaining. The root `.env` key had exhausted its $30 cap; the updated key in `backend/.env` has about $29.44 remaining.
- Fixed dotenv precedence so local `backend/.env` overrides root `.env` values while inherited process environment still takes precedence.
- Built and verified the isolated PDF2 index: 15 documents, 280 chunks, 1,536-dimensional vectors. The application now routes normal retrieval and document listing to PDF2; legacy tables still contain 14 documents / 242 chunks and remain untouched.
- Disabled manual uploads and individual document deletion so the active corpus cannot drift from the `pdf2/` source.
- Created `agent.md`, `plan.md`, `progress.md`, and `loop.md` to guide the later implementation and keep work active until acceptance criteria are met.
- The app now uses the PDF2 tables for `/api/query` and `/api/documents`; legacy tables remain stored but are not queried.
- Manual uploads and individual document deletion are disabled to keep PDF2 as the single corpus source.

## Findings to carry into implementation

- The local `pdf2/` folder contains 15 PDFs. The prior re-ingestion log shows 14 PDFs and 242 chunks ingested from `pdfs/`.
- `pdf2/` includes Quality Policy and Information Security Policy; it does not appear to include the Parental Policy Handbook that is present in the old `pdfs/` set. This changes which questions can be answered.
- The old `reingest.py` cleared the active tables before processing. It has been replaced with PDF2 preflight plus an isolated candidate build; the compatibility seeder now uses the same staged-only workflow.
- The query handler now decomposes retrieval into focused searches, merges semantic and PostgreSQL full-text candidates, and returns a fixed not-found response when no chunks qualify.
- The model-based `CHAT`/`RETRIEVE` routes remain in place; CHAT skips DB/retrieval, while RETRIEVE searches policy evidence.
- Chunking now preserves extracted line structure, uses an approximate token budget, and no longer drops standalone numeric lines.
- Existing sample-question and unanswered-question files provide evaluation cases, including scenarios and known unsupported questions.
- Current configured embedding is `openai/text-embedding-3-small` (1,536 dimensions); configured chunking is 512 words/64-word overlap, top-K 5, and threshold 0.3.
- PDF2 has 15 PDFs / 240 pages. PyMuPDF plus RapidOCR preflight processed all documents; OCR checks remain part of preflight for future source changes.
- The handbook is V15 dated 20 Aug 2019, while 2025–26 insurance guides and an undated Travel Process PDF coexist. The handbook and travel guide contain different per-diem settlement windows (one vs two weeks); source precedence needs confirmation.
- The previous handbook cleaner deleted standalone numeric lines; it now preserves numeric table values and removes only known page-counter patterns. PDF2's Per Diem file does not include country-specific daily rates; the Travel PDF does include other facts such as a two-week settlement and per-diem day definition.
- The 110 supplied questions are not a complete answer-key dataset. Existing Markdown expected answers need validation against approved/current source documents before serving as gold labels.
- Exact vector search is currently used against the local 242-chunk corpus, so an ANN-index migration is not currently needed.

## Open decisions — resolve before dependent work

1. **Replacement scope:** Recommended: delete only indexed `documents`/`chunks` for the old corpus; retain source files, conversation history, schema, and the database volume. Confirm this before the index replacement.
2. **Parental policy:** Is the absence of the Parental Policy Handbook from `pdf2/` intentional? If yes, answers that depend only on that document must be unavailable until it is added to the approved corpus.
3. **PDF upload endpoint:** Should manual uploads remain an allowed source outside `pdf2/`, or should the indexed corpus be restricted to `pdf2/` only? Recommended for this task: `pdf2/` is the sole bulk/replacement corpus; decide whether to disable/restrict uploads or explicitly leave them as a separate permitted source.
4. **Scenario answers:** Recommended: apply documented rules to the facts in a scenario, with citations; ask a focused follow-up if a material fact is missing; do not make unsupported HR judgments. Confirm if a stricter “quote rules only” style is preferred.
5. **Embedding migration:** An existing `plan.md` proposed switching to local EmbeddingGemma and 768-dimensional vectors. That is a separate breaking migration. The current corpus-replacement plan keeps the current 1536-dimensional OpenRouter embeddings unless the user explicitly includes that migration.
6. **Source precedence:** Confirm which policy version governs when the 2019 handbook differs from 2025–26 or newer documents, including travel/per-diem deadlines and ESK vs PIL applicability.
7. **Missing source PDFs:** Confirm whether excluding the Parental Policy Handbook and the country-by-country Per Diem rate card from `pdf2/` is intentional. Questions that depend on absent documents must receive a not-found response.

## Implementation progress

- [ ] User reviews the architecture findings and confirms source precedence and policy for missing PDFs/rate cards.
- [ ] Resolve open decisions that affect source scope, answer behavior, and destructive replacement.
- [x] Make ingestion reliably select and validate only the approved `pdf2/` inputs.
- [x] Resolve local dotenv precedence and build the 280-chunk PDF2 index in separate tables.
- [x] Switch app query/document-list paths to PDF2 only; keep legacy tables stored and unused.
- [ ] Evaluate the active PDF2 index against the supplied questions.
- [ ] Show evaluation/source-conflict results and wait for explicit confirmation before deleting the legacy index.
- [ ] Improve retrieval and grounding for paraphrased, multi-part, and situation-based questions.
- [x] Remove hard-coded greeting phrases and implement model-assisted CHAT/RETRIEVE routing with safe invalid-output fallback.
- [x] Verify through query-handler tests that CHAT replies skip DB/retrieval while RETRIEVE questions run RAG.
- [x] Add deterministic no-chunk abstention and inline source citation instructions.
- [ ] Run tests and the agreed evaluation set; fix failures and repeat relevant checks.
- [ ] Verify indexed document inventory and counts against the approved `pdf2/` corpus.
- [ ] Update user-facing setup/deployment instructions and this progress file with actual results.

## Current next action

Run retrieval/evaluation against the active PDF2 tables. Resolve policy-version precedence before legacy cleanup; after results are reviewed, wait for explicit confirmation before deleting legacy.

## Retrieval table map

- Current production `/api/query`: `RAGService(db)` → `chunks_pdf2_stage` + `documents_pdf2_stage` (PDF2, 15 documents / 280 chunks).
- Legacy, not queried: `chunks` + `documents` (14 documents / 242 chunks).
- After evaluation and explicit confirmation: back up and delete only the legacy tables. No dual-corpus retrieval or table rename is needed.

## Verification log

- Pre-commit verification (2026-10-26): **28 backend tests passed**, **2 frontend stream tests passed**, and frontend TypeScript checking passed. The backend tests required a rerun outside the sandbox to access pytest's temporary directory. Added generated `.coverage` files to `.gitignore`.

- 2026-10-26 sources display fix: restored the hidden sources panel in `frontend/app/page.tsx` (document names, page references, excerpts), with an accessible expand/collapse control. Added `frontend/lib/ndjson.ts` so split network packets cannot discard the citation metadata event.
- `node --test scripts/tests/frontend-ndjson.test.mjs`: **2 passed**, covering fragmented citation JSON, split UTF-8 characters, combined records, blank lines and a final record without a newline. `npm --prefix frontend run type-check` passed.
- Rebuilt/restarted only the Docker frontend with `docker compose -f docker/docker-compose.yml up -d --build --no-deps frontend`; production compilation/type checks passed. Existing PDF2 database inventory remains 15 documents / 280 chunks. No re-indexing or legacy cleanup was performed.

- `python -m pytest -o addopts= backend/tests -q` — **17 passed** (one existing SQLAlchemy deprecation warning).
- `backend/.venv/Scripts/python.exe -m pytest backend/tests -q` — **27 passed** (two existing Starlette/SQLAlchemy deprecation warnings).
- Plain `python -m pytest ...` uses `pyproject.toml` coverage add-ons unavailable in this environment; overriding `addopts` ran the tests successfully.
- `python -m black --check ...` could not run because Black is not installed in the current Python environment.
