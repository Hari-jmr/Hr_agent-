# Plan: Replace HR Policy Index with `pdf2/` and Improve Grounded Answers

**Status:** The application uses PDF2 (15 documents / 280 chunks). On 2026-10-26, the user explicitly requested legacy deletion; `documents` and `chunks` were removed after source validation and a verified backup. Startup no longer recreates them. Policy-version precedence and answer-quality evaluation remain open.

## Goal

Use only the approved PDFs in `pdf2/` for the replacement batch index, and make the HR chatbot answer direct, indirect, and situation-based questions from policy evidence. When the documents do not support an answer, the chatbot must say so rather than guess. Keep authentication, login, and session behavior unchanged.

## Current-state findings

- The original `scripts/reingest.py` was hard-coded to `pdfs/` and deleted the active corpus before ingestion. It now preflights `pdf2/` and writes to isolated staging tables.
- The original `scripts/seed-embeddings.py` defaulted to `pdfs/`, skipped by filename, and imported a missing `Config`; it is now a compatibility entry point to the staging-only workflow.
- The query handler now returns a deterministic not-found response when no chunks pass retrieval; it does not call the answer model with empty context.
- Before the routing-only change, `backend/services/intent_router.py` used exact short allowlisted social/meta phrases for `CHAT`; every other message defaulted to `POLICY` and went through the DB/embedding/vector path.
- The updated router uses OpenRouter to choose only `CHAT` or `RETRIEVE`. CHAT returns a natural response (including greeting, scope redirection, or clarification) without DB/embedding/vector retrieval. RETRIEVE covers HR policy questions and situations and goes through retrieval. Invalid classification output falls back to RETRIEVE.
- Current chunking preserves extracted lines under an approximate token budget, but does not yet merge section context across pages or fully reconstruct table structure.
- The prior re-ingestion log reports 14 PDFs and 242 chunks from `pdfs/`. The local `pdf2/` folder contains 15 PDFs, including Quality Policy and Information Security Policy, and appears to omit the Parental Policy Handbook that was in the old set.
- `unanswered_questions.md` and the sample question documents include indirect, scenario-based, supported, and unsupported cases suitable for evaluation.

## RAG architecture audit — supplied question sets and PDF2

The two supplied DOCX files contain roughly 110 questions (37 in the first set and 73 in the second). They cover direct policy lookups, paraphrases, multi-condition situations, branch-specific benefits, referrals, and sequential travel/per-diem processes. They are question prompts, not a fully annotated gold-answer set; the Markdown companion has some expected answers, but those must be checked against the authoritative PDFs and effective dates before being treated as truth.

### Findings from the current implementation and local corpus

- Current config is `openai/text-embedding-3-small` at 1,536 dimensions, 512 **words** per chunk, 64-word overlap, top-K 5, and similarity threshold 0.3. The prior unanswered-question notes say 0.2/top-K 10 resolved 9 of 41 misses, but that is not a controlled comparison. Do not change embedding models or blindly lower the threshold before evaluating retrieval on these sets.
- The prior re-ingestion log has 242 chunks. `scripts/init-db.sh` creates an IVFFlat cosine index with `lists=100`; verify whether the active DB actually has it. For a corpus of only a few hundred vectors, exact cosine search is likely the better-recall and simplest choice; if approximate search remains, tune lists/probes and measure recall instead of assuming defaults are suitable.
- Read-only inspection of the configured local `hr_agent` database found 14 documents and 242 chunks, with no vector ANN index (only the chunk primary-key index). Exact cosine search is therefore the current behavior and is appropriate at this corpus size; do not add an approximate index during replacement without measured need.
- The production chunker is not semantic despite its method name: it splits text by word count separately on each page. It does not preserve section hierarchy, table rows, or page ranges, and most short pages become independent chunks. Scenario questions can need several independent rules, but current query processing condenses to one search query and retrieves only top-K chunks.
- PyMuPDF finds text on 239 of the 240 PDF2 pages, but image pages can contain additional content. Visual inspection confirmed the Travel form screenshots contain details not in its text layer. RapidOCR fallback now extracts these pages and the full 15-PDF preflight succeeds.
- The original cleaner removed standalone numeric lines; it now preserves those values and removes only recognized page/header patterns.
- `JMR_Employee_Handbook.pdf` is version 15 dated 20 Aug 2019. It says some travel/per-diem claims are due within one week, while `Travel Process & Guidelines.pdf` says per-diem settlement is due within two weeks and has no clear effective date in its filename. Do not merge these into one rule: preserve source/version metadata and surface the conflict until an owner confirms precedence/current validity.
- The 2025–26 ESK/PIL health documents are different plans (employee/spouse/children vs parents/in-laws). Their branch distinctions must survive retrieval and answers should ask which plan applies if the employee's group is unknown. Some handbook/manual text also contains embedded policy-period labels that appear older than the filenames; verify effective dates with the policy owner rather than silently choosing a date.
- `pdf2/` lacks a separate Parental Policy Handbook from the old source set. It does have maternity/paternity leave material in the 2019 employee handbook and maternity insurance material in the ESK documents; these are not interchangeable with a separate parental-policy guide.
- The specific per-country daily per-diem rate (including Saudi Arabia) is not present in the inspected Per Diem PDF2 document. Correct behavior is “not found” unless an authoritative rate card is added. Re-indexing cannot recover absent content.
- Embeddings are now sent in batches with response count/order and 1,536-dimension validation.
- The first candidate attempt used the exhausted root `.env` key because dotenv precedence masked the updated `backend/.env` key. Config loading now prioritizes the backend `.env` over root `.env` while preserving inherited process variables. The updated key successfully built the candidate.
- Candidate staging verification found 15 documents and 280 chunks with one consistent vector dimension. The active tables remain at 14 documents and 242 chunks.
- Current citation metadata stores one page number per chunk. If chunks span pages after improved section-aware chunking, store start/end page provenance. Current retrieval attaches all selected citations whether or not the answer uses each source; evaluation must check citation support, not only citation presence.

### Recommended architecture changes, in order

1. **Keep the embedding model for this pass.** Use the same `text-embedding-3-small` model and 1,536 dimensions for corpus and queries. First fix text coverage, retrieval recall, and evidence handling; compare alternate models only if the annotated evaluation set shows a remaining embedding-specific gap.
2. **Make extraction quality a precondition to indexing.** Extract text/layout per page; detect image-heavy pages with little text; OCR those pages (initially the Travel screenshots) and report pages that remain unreadable. Preserve headings, table row/column relationships, list conditions, section names, source filename, and page/page-range. Do not mark a PDF successfully indexed if important pages yielded no usable content.
3. **Use section-aware/token-aware chunks.** Preserve headings with their rules, keep table rows together, split only long sections by actual token budget with overlap, and avoid embedding title-only/near-empty chunks. Store source page ranges and document version/effective-date metadata.
4. **Improve retrieval for scenarios.** Decompose a compound scenario into its distinct policy questions, retrieve per subquestion, merge/deduplicate and rerank evidence. Add lexical/keyword retrieval for exact policy terms, numbers, acronyms, and table entries alongside semantic retrieval. Cap results per document so a long handbook cannot crowd out a second relevant policy.
5. **Calibrate the vector search.** Measure Recall@K/answer-evidence coverage on the 110 questions. For the current small corpus, use exact cosine search or prove the IVFFlat/HNSW configuration reaches comparable recall. Tune top-K and the threshold from labeled positives and true no-answer cases.
6. **Enforce evidence outcomes in code.** If retrieval has no adequate evidence, return a deterministic “I don’t know from the currently indexed policies” response without calling the answer LLM. For partial evidence, answer only the supported parts; for conflicting editions/plans, cite and disclose the conflict; for missing material facts, ask a focused follow-up. Prior assistant messages can resolve references but are not evidence.
7. **Build a gold evaluation set before trusting expected answers.** For each question, record expected answerability, authoritative source/version/page(s), supported facts, and any clarifying field (e.g. ESK vs PIL). Evaluate retrieval hits, factual correctness, citation precision, and abstention separately. Include exact screenshots/OCR facts and true absent questions.

**Embedding decision:** no embedding model/dimension change is recommended at this stage. The evidence points first to extraction gaps (notably travel screenshots), source/version conflicts, overly simple chunking, and retrieval/index calibration.

## Scope and safety boundaries

- Batch replacement source: `pdf2/` only, after confirming the user intends the Parental Policy Handbook omission.
- Build PDF2 into isolated `documents_pdf2_stage`/`chunks_pdf2_stage` tables. Keep the legacy `documents`/`chunks` corpus active and untouched while the candidate is indexed and evaluated.
- After the candidate passes preflight and question-set evaluation, show the user the inventory/results and wait for explicit confirmation. Only then back up the old index, atomically promote the candidate, and delete the old active index; do not delete it merely because staging succeeded.
- Recommended deletion scope: replace indexed HR `documents` and `chunks` only. Preserve `pdfs/`, `pdf2/`, conversation history, unrelated application data, schema, and the database volume.
- Validate the active database target and source files, and create/verify a recovery point before deleting old index rows. Do not clear the old index before preflight succeeds.
- Keep the current embedding provider/model and 1536-dimensional schema for this corpus switch. Do not combine it with the separate local EmbeddingGemma migration below without explicit approval.
- Confirm whether the PDF upload API remains an allowed source outside the batch corpus. Do not silently allow uploads to undermine a stated `pdf2/`-only policy.
- Leave authentication, Odoo access, chat UI, and session behavior unchanged except where required to preserve existing response compatibility.

## Routing decision: model classification, enforced actions

Do not hard-code greeting/thanks phrase lists. OpenRouter classifies every incoming message and returns one validated action label plus a short user-facing reply for CHAT. The application still enforces what each label is allowed to do; the model does not decide policy facts.

- `CHAT`: conversation that does not need a JMR policy lookup. This includes greetings, casual conversation, assistant-capability questions, a brief redirect for unrelated requests, and a clarification question when the user's intent is unclear. Return the model's short reply without DB/embedding/vector search.
- `RETRIEVE`: any direct/indirect JMR HR policy question, scenario, or policy follow-up. Run retrieval before generating any policy answer.

Only two labels are needed because they represent the operational decision: search policy evidence or answer conversationally. “Out of scope” and “clarify” are response styles within CHAT, not separate retrieval paths. The labels are not lists of greeting phrases. `RETRIEVE` names the required action rather than using `POLICY` as an ambiguous label.

Validate the classifier's JSON and allowed label in application code. For malformed output, timeout, or unknown labels, fall back to `RETRIEVE` so a possible HR question is not answered from model memory. Keep the separate deterministic no-evidence answer guardrail after retrieval. This approach sends a classifier call for every message; account for its latency/cost and make sure the configured OpenRouter model supports the required structured JSON response.

## Active vs candidate retrieval and promotion

- Normal `/api/query` now constructs `RAGService(db)` with the default `corpus="active"`, which resolves only to `documents_pdf2_stage` and `chunks_pdf2_stage`. The legacy `documents`/`chunks` tables are not queried.
- `/api/documents` lists the PDF2 corpus. Manual upload and individual document deletion are disabled so the active index remains a mirror of the `pdf2/` folder.
- After candidate evaluation and the user's confirmation, create/verify a backup of the old `documents`/`chunks` data, then drop only those legacy index tables. The active PDF2 table names remain unchanged; no table rename or dual-corpus search is needed.
- Smoke-test `/api/query` and `/api/documents` before cleanup. Do not drop the database volume, source PDFs, or conversation history.

## Phase 0 — Confirm decisions and baseline

1. Confirm indexed-row deletion scope and preserve source PDFs/history/database volume.
2. Confirm whether `pdf2/` intentionally excludes the Parental Policy Handbook.
3. Keep manual uploads disabled; all indexed PDF content must come from `pdf2/`.
4. Confirm the recommended scenario behavior: apply documented policy conditions to stated facts, ask focused questions when a material fact is missing, and never invent an outcome.
5. Confirm the two routing actions: CHAT (natural response, no retrieval) and RETRIEVE (HR policy evidence required). The model may clarify or redirect within its CHAT response. Use conversation history to resolve likely policy follow-ups; a greeting attached to an HR question must still take RETRIEVE.
6. Record the current database target, current indexed document inventory, model identity/dimension, configured retrieval threshold/top-K, and current test baseline without exposing credentials.
7. Approve/document source precedence for handbook vs newer travel/benefits guides and confirm whether the separate Parental Policy Handbook and per-country per-diem rate card are intentionally excluded.

**Exit criteria:** decisions are recorded; there is a clear and safe source/deletion boundary.

## Phase 1 — Reliable source selection and ingestion

1. Make the replacement command explicitly select `pdf2/`; remove implicit fallback to `pdfs/` for replacement runs.
2. Repair/replace the unreliable seed-script import and ensure incremental ingestion cannot masquerade as a full replacement.
3. Preflight sorted `*.pdf` inputs: check expected count/inventory, readability, extracted text/page coverage, empty documents, duplicate names/content where useful, and parse errors.
4. Make each document ingestion all-or-nothing. Record per-file status, page count, chunk count, and actionable errors; do not silently skip a failed PDF.
5. Use a staged replacement or a backed-up, recoverable transaction/process so the old index is not destroyed before new inputs are validated and ingestion can complete.
6. Preserve page/document/version provenance for citations. OCR is required for screenshot-heavy pages in Travel Process & Guidelines; include extraction coverage checks and report unreadable pages before indexing.

**Exit criteria:** repeatable, explicit `pdf2/` ingestion; reliable failure reporting; a safe recovery path.

## Phase 2 — Retrieval for indirect and situation-based questions

1. Use the OpenRouter classifier for every message; do not route by hard-coded greeting phrases. Enforce the two actions defined above. Use conversation history to resolve a likely HR follow-up; if meaning remains unclear, CHAT can ask a focused clarification. A greeting attached to an HR question must still take the retrieval path.
2. Keep query embedding compatible with the current indexed vectors; do not change provider/model/dimensions in this pass without evaluation evidence.
3. For a scenario, identify the actual policy issues, entities, time/location/employee category, stated conditions, and question(s) being asked.
4. Retrieve evidence per issue rather than relying on one embedding for a long compound scenario. Resolve pronouns/follow-ups using conversation context, but do not treat prior assistant answers as evidence.
5. Combine semantic retrieval with lexical/phrase matching; rerank using relevance, plan/employee applicability, and policy-specific terms. Keep retrieval bounded and configurable.
6. Preserve exact eligibility requirements, exceptions, deadlines, approval steps, effective dates, and source-specific distinctions. Do not turn a related passage into proof of an unstated rule.
7. Calibrate similarity/evidence thresholds and exact-vs-approximate vector search on the annotated evaluation set after the corpus is indexed. The current threshold may not be appropriate for the final corpus; never lower it blindly just to increase answer rate.

**Exit criteria:** routing tests prove CHAT skips DB, embedding, and vector search; RETRIEVE and policy follow-ups retrieve evidence. Paraphrases and multi-part scenarios retrieve the necessary evidence without introducing unrelated context.

## Phase 3 — Answer guardrails and citations

Implement deterministic handling for these evidence states:

- **Supported:** concise answer to the exact question, applying only documented rules; cite the supporting PDF and page(s).
- **Conditional/missing facts:** ask a focused clarifying question or state the supported conditional branches; do not assume missing employee facts.
- **Partially supported:** answer the established portion, label what cannot be determined, and cite the supported portion.
- **No adequate evidence:** return a fixed, clear “I don’t know based on the currently indexed policies” response without asking the LLM to answer from an empty/irrelevant context; do not attach misleading citations.
- **Conflicting documents:** surface the conflict and cite both sources; do not choose a winner absent an explicit precedence/effective-date rule.
- **Non-policy small talk/out-of-scope:** retain brief conversational behavior, but never present general model knowledge as JMR policy.

Additional protections:

- Treat retrieved PDF text and conversation history as untrusted data, not instructions.
- Keep policy answers grounded only in retrieved current-corpus passages. Prior assistant text can help resolve a follow-up reference but is never authoritative evidence.
- Require citations for policy claims and ensure citation metadata identifies actual supporting pages.
- Avoid exposing sensitive employee information or secrets in prompts, outputs, and logs.
- Preserve the existing streaming response contract unless tests demonstrate a necessary compatible extension.

**Exit criteria:** answer behavior is controlled by evidence state, and every policy claim is traceable.

## Phase 4 — Evaluation and calibration

Use the sample-question documents and `unanswered_questions.md` as a starting set. Include:

- Direct supported questions with expected rule/number/date and source page.
- Paraphrases and scenarios combining multiple rules (e.g. certification + resignation, urgent leave + notice period, travel expense deadline).
- Questions with missing material facts that should trigger clarification/conditional answers.
- Truly absent answers (e.g. topics absent from the selected corpus) that must return “I don’t know.”
- Partial evidence, conflicting policy editions/entities, follow-up pronouns, greetings, out-of-scope questions, and prompt-injection text in retrieved excerpts.
- Explicit routing assertions: CHAT responses (including greetings, scope redirects, and clarification questions) do not call DB/embedding/retrieval; direct HR, scenario, mixed greeting+HR, and history-resolved HR follow-up questions do. Unresolved messages may be clarified in CHAT.
- PDF parsing cases for tables, short documents, empty pages, and scanned pages if present.

Check retrieval evidence and final answer separately: relevant pages were found, claims match excerpts, no unsupported rules were introduced, and citations are accurate. Track false abstentions separately from hallucinations. Tune chunking/retrieval based on measured failures.

**Exit criteria:** tests demonstrate both useful scenario reasoning and reliable abstention; existing tests continue to pass.

## Phase 5 — Replace, verify, document

1. PDF2 is built in isolated tables and is now the app's active retrieval corpus; legacy tables remain stored but unused.
2. Run the evaluation set against the active PDF2 tables; inspect retrievals, answers, and citations.
3. Present inventory, extraction/OCR warnings, evaluation results, and source conflicts to the user; wait for explicit confirmation before deleting legacy tables.
4. Back up the old index and drop only legacy `documents`/`chunks` as authorized. PDF2 remains active in its existing tables.
5. Verify inventory, chunk counts, embedding dimensions, retrieval behavior, login, sessions, chat streaming, and document listing.
6. Update setup/deployment docs for the PDF2-only active corpus and legacy-index removal.
7. Record final counts, checks, content gaps, and failures in `progress.md`.

**Exit criteria:** all completion criteria in `loop.md` pass, with no unreported partial index or unresolved implementation blocker.

## Open decisions

See `progress.md`. Do not perform destructive corpus replacement while the source/deletion scope or target database is ambiguous.

## Deferred reference: existing local EmbeddingGemma migration proposal

The original contents of this file proposed switching embeddings to local EmbeddingGemma 2 (768 dimensions), changing dependencies/config/schema, migrating existing vectors, and tuning worker/RAM usage. That is a separate breaking migration and is **not part of this approved corpus/grounding plan** unless the user explicitly requests it. It has been retained below as reference so its prior details are not lost.

---

# Deferred Plan: Local EmbeddingGemma 2 for hrms v1

Source project (reference): `D:\...\hari\project\gemma2`
Target project: `D:\...\hari\hrms v1`

## Untouched (explicitly NO changes)

- `backend/api/routes/auth.py`, `backend/services/auth_service.py`, `backend/api/deps.py`
- Odoo DB login config (`DB_HOST/PORT/NAME/USER/PASSWORD`), session handling
- `backend/services/intent_router.py` and its tests
- Frontend chat/citation components (streaming ndjson contract stays the same)
- `OpenRouterClient.stream_chat` (OpenRouter still generates answers)

## 1. New embedder module — `backend/services/embeddings.py`

- Lazy CPU `SentenceTransformer` singleton, mirroring gemma2 `app/main.py get_encoder()`:
  - `SentenceTransformer(EMBEDDING_MODEL_PATH, local_files_only=True, trust_remote_code=False,`
    `config_kwargs={"vision_config": None, "audio_config": None}, model_kwargs={"torch_dtype": torch.float32}, device="cpu")`
- Prompt names: documents `prompt_name="Document"`, queries `prompt_name="SearchQuery"`,
  always `normalize_embeddings=True`, dtype float32, 768 dims.
- `embedding_model_id()` = model directory name + hash (like gemma2's versioned-path identity);
  stored per document to detect model changes.
- Batch encode: `encode(list_of_texts)` per document (one pass, not per-chunk HTTP calls).

## 2. Config and dependencies

- `backend/requirements.txt`: add `sentence-transformers>=6,<7` (pulls torch; 6.1.0 needed —
  the Kaggle checkpoint is ST 6.x format).
- `backend/core/config.py`: add
  - `EMBEDDING_MODEL_PATH = os.getenv('EMBEDDING_MODEL_PATH')`
- `.env` / `.env.example`: add `EMBEDDING_MODEL_PATH=` (point at gemma2 cache dir or a local
  copy — decision below), mark `OPENROUTER_EMBED_MODEL` as deprecated (unused after migration).
- Model path decision:
  - Option A (default): reuse `D:\...\project\gemma2\models\kaggle-cache\models\google\embeddinggemma-2\transformers\embeddinggemma-2\1`
  - Option B: copy ~1.4 GB into `hrms v1/models/` for self-containment

## 3. Schema migration (BREAKING: 1536 -> 768 dims)

In `backend/main.py` models:
- `Chunk.embedding = Vector(768)`
- `Document.embedding_model` default -> local model id
- `Document` add `sha256 = Column(String)` (+ unique index) for dedupe/replace

One-time script `scripts/migrate_embeddings.py` (idempotent):
1. `TRUNCATE chunks; DELETE FROM documents;` (old 1536-dim vectors are useless with new model)
2. `ALTER TABLE chunks ALTER COLUMN embedding TYPE vector(768);`
3. `DROP INDEX IF EXISTS chunks_embedding_idx;` recreate:
   `CREATE INDEX chunks_embedding_idx ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);`
4. `ALTER TABLE documents ADD COLUMN IF NOT EXISTS sha256 TEXT;`
   `CREATE UNIQUE INDEX IF NOT EXISTS documents_sha256_idx ON documents (sha256);`
5. Update `scripts/init-db.sh` for fresh installs (vector(768), sha256 column, new default model name).

## 4. Retrieval + ingestion switch (`backend/main.py`)

- `RAGService.retrieve_relevant_chunks`: replace `llm_client.get_embedding(query)` with
  local embedder (`SearchQuery` prompt). Keep cosine `<=>` SQL, similarity = 1 - distance.
  NOTE: `SIMILARITY_THRESHOLD=0.7` was tuned for text-embedding-3-small; after re-ingest, run
  the sample question sets and adjust (keep it env-configurable).
- Model-identity guard (gemma2 style): store `embedding_model` per document; on retrieval, if a
  matched document's model != current `embedding_model_id()`, exclude it / raise a clear
  "re-index required" error instead of silently returning garbage.
- SHA-256 dedupe/replace on upload (gemma2 style): hash file bytes; if a document with that hash
  exists, reuse its `document_id`, delete its chunks, re-extract/re-embed, overwrite the stored
  PDF; response/audit notes `replaced: true`.
- `ingest_document` (background task): use batch local embedding; keep single-commit per document
  transactional behaviour (all chunks or none).
- `upload_document`: currently writes to `/tmp/{doc_id}_...` — move to a persistent
  `data/documents/{doc_id}.pdf` so re-indexing later is possible (parity with gemma2 `data/`).

## 5. Re-index all PDFs

- Update `scripts/reingest.py`: use local embedder + sha256 (replaces the OpenRouter path);
  wipe-and-reingest all `pdfs/*.pdf` (15 files).
- Run: `backend\.venv\Scripts\python scripts\reingest.py` (expect several minutes on CPU).
- Log per-doc chunk counts + a few sample similarity scores to calibrate the threshold.

## 6. Worker/RAM constraint

- Current `uvicorn.run(workers=int(WORKERS, default 4))`: each worker loads its own ~3 GB torch
  copy -> 12 GB+ on a 15 GB machine. Set default `WORKERS=1` for local/dev.
- Later at deploy scale: keep 1 embed model per box, or split embedding into a tiny sidecar
  service; revisit with vLLM/GPU server then.

## 7. Verification checklist

- [ ] `pytest backend/tests` (intent router tests still green)
- [ ] Fresh schema script runs clean on `hr_agent` DB
- [ ] `reingest.py` indexes all 15 PDFs; `SELECT count(*) FROM chunks` > 0, all 768-dim
- [ ] `/api/query` returns cited answers for known questions from both sample question docs
- [ ] Similarity scores logged; `SIMILARITY_THRESHOLD` adjusted if 0.7 is off for EmbeddingGemma
- [ ] Upload same PDF twice -> one document (replaced, same id)
- [ ] Model-identity guard: rename EMBEDDING_MODEL_PATH version -> retrieval errors clearly
- [ ] Login/logout/session unchanged and working
- [ ] No new URLs/keys in code; all via `.env`

## Out of scope (future)

- Docling/OCR parser option for scanned policy PDFs (gemma2 has it; hrms uses PyMuPDF text only)
- Streaming answer prompt rework with inline [1],[2] citations (keep current pipeline for now)
- Background job queue for large uploads (gemma2 TODO too)
- GPU/vLLM deployment tuning
