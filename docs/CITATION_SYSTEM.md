# Citation System

## Design

Each answer includes structured citations linking back to source documents.

## Citation Model

```python
class Citation(BaseModel):
    document_id: str
    document_name: str
    page_number: Optional[int]
    chunk_id: str
    content_preview: str  # First 150 chars
    confidence_score: float  # 0-1 similarity score
```

## Frontend Display

Citations appear as expandable badges below assistant messages:
- Document name + page number
- Confidence percentage
- Expand to show content preview
- Link to view full source document

## Tracking

- Citations stored in `conversation_history` table as JSON
- Used for audit logs and analytics
- Enables "click to verify" workflow
