import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from main import SessionLocal, RAGService, llm_client, config
import asyncio

async def test():
    print('DB URL:', config.DATABASE_URL)
    print('LLM Model:', config.OPENROUTER_LLM_MODEL)
    print('API Key exists:', bool(config.OPENROUTER_API_KEY))
    
    db = SessionLocal()
    try:
        rag = RAGService(db)
        print('Testing retrieve_relevant_chunks...')
        chunks = await rag.retrieve_relevant_chunks('What is the leave policy?', top_k=3)
        print('Retrieved', len(chunks), 'chunks')
        for c in chunks[:2]:
            doc_name = c['document_name']
            preview = c['content'][:60]
            print('  -', doc_name, ':', preview, '...')
        
        context, citations = await rag.format_context_with_citations(chunks, 'test')
        print('Formatted', len(citations), 'citations')
        
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

asyncio.run(test())
