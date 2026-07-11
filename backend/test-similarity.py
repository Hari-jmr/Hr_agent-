import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from main import SessionLocal, llm_client
import asyncio
import numpy as np

async def test():
    db = SessionLocal()
    try:
        # Get embedding for a test query
        query = 'What is the probation period duration?'
        query_embedding = await llm_client.get_embedding(query)
        query_vec = np.array(query_embedding, dtype=np.float32)
        query_embedding_str = '[' + ','.join(str(x) for x in query_vec.tolist()) + ']'
        
        # Run raw SQL with no threshold filtering
        from sqlalchemy import text
        sql = text(f"""
            SELECT 
                c.id,
                d.filename,
                c.content,
                c.embedding <=> '{query_embedding_str}'::vector as distance
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            ORDER BY c.embedding <=> '{query_embedding_str}'::vector
            LIMIT 5
        """)
        
        result = db.execute(sql)
        print(f'Query: "{query}"')
        print(f'Top 5 chunks (raw distances):')
        for row in result.mappings():
            dist = float(row['distance'])
            sim = max(0.0, 1.0 - dist)
            print(f'  sim={sim:.3f} | {row["filename"]}')
            content = row["content"][:120].encode('ascii', 'ignore').decode()
            print(f'    {content}...')
            print()
    finally:
        db.close()

asyncio.run(test())
