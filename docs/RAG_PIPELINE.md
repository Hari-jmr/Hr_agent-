# RAG Pipeline

## Overview

The RAG (Retrieval-Augmented Generation) pipeline consists of:

1. **Document Ingestion**
   - PDF parsing with PyPDF2
   - Semantic chunking (512 tokens, 64 overlap)
   - Embedding generation via OpenRouter
   - Storage in pgvector

2. **Query Processing**
   - Embed user question
   - Similarity search in pgvector
   - Re-rank by confidence
   - Format context with citations

3. **Answer Generation**
   - Send context + question to OpenRouter LLM
   - Stream response back to frontend
   - Include citation metadata

## Chunking Strategy

```python
def semantic_chunk(text: str, chunk_size: int = 512, overlap: int = 64):
    chunks = []
    words = text.split()
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        chunk_text = " ".join(chunk_words)
        
        if chunk_text.strip():
            chunks.append({
                "content": chunk_text,
                "page_number": page_num,
                "chunk_index": len(chunks)
            })
    
    return chunks
```

## Similarity Search

```sql
SELECT 
    id, 
    document_id, 
    content,
    (embedding <-> query_embedding) as distance
FROM chunks
ORDER BY embedding <-> query_embedding
LIMIT 5;
```

## Re-ranking

Chunks are re-ranked by:
- Semantic similarity score
- BM25 keyword match
- Page position weighting
