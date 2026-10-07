# API Reference

## Endpoints

### `GET /api/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "llm_model": "anthropic/claude-3-5-sonnet"
}
```

---

### `POST /api/query`
Process user query with RAG and streaming response.

**Request:**
```json
{
  "question": "What is my notice period?",
  "conversation_history": [
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello! How can I help?"}
  ],
  "session_id": "session-123"
}
```

**Response (Streaming NDJSON):**
```
{"type":"start","citations":[...]}
{"type":"chunk","content":"The notice period is "}
{"type":"chunk","content":"30 days"}
{"type":"end"}
```

---

### `GET /api/documents`
List all ingested documents.

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

---

### `POST /api/documents/upload`
Upload and ingest a PDF document.

**Request:** Multipart form-data with `file` field.

**Response:**
```json
{
  "document_id": "doc_1704882600",
  "filename": "Leave_Policy.pdf",
  "status": "queued_for_ingestion"
}
```

---

### `DELETE /api/documents/{document_id}`
Delete a document and its embeddings.

**Response:**
```json
{
  "message": "Document deleted",
  "document_id": "doc_1"
}
```
