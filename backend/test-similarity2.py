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
        query = 'What is the probation period duration?'
        query_embedding = await llm_client.get_embedding(query)
        query_vec = np.array(query_embedding, dtype=np.float32)
        query_embedding_str = '[' + ','.join(str(x) for x in query_vec.tolist()) + ']'
        
        from sqlalchemy import text
        sql = text(f"""
            SELECT 
                c.id,
                d.filename,
                c.content,
                c.chunk_index,
                c.page_number,
                c.embedding <=> '{query_embedding_str}'::vector as distance
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE d.filename LIKE '%Employee Handbook%'
            ORDER BY c.embedding <=> '{query_embedding_str}'::vector
            LIMIT 10
        """)
        
        result = db.execute(sql)
        print(f'Query: "{query}"')
        print(f'Top 10 chunks from Employee Handbook:')
        for row in result.mappings():
            dist = float(row['distance'])
            sim = max(0.0, 1.0 - dist)
            content = row["content"][:150].encode('ascii', 'ignore').decode()
            print(f'  sim={sim:.3f} | chunk={row["chunk_index"]} page={row["page_number"]} | {content}...')
            print()
    finally:
        db.close()

asyncio.run(test())
