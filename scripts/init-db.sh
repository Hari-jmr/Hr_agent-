# scripts/init-db.sh
#!/bin/bash

"""
PostgreSQL Database Initialization Script
Sets up pgvector extension and creates schema for HR Agent Bot
"""

set -e

POSTGRES_USER=${POSTGRES_USER:-admin}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-secure_password}
POSTGRES_DB=${POSTGRES_DB:-hr_agent}
POSTGRES_HOST=${POSTGRES_HOST:-localhost}
POSTGRES_PORT=${POSTGRES_PORT:-5432}

echo "🔧 Initializing PostgreSQL for HR Agent Bot..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d postgres -c "SELECT 1" 2>/dev/null; do
  sleep 1
done

echo "✅ PostgreSQL is ready!"

# Create database if not exists
echo "📦 Creating database '$POSTGRES_DB'..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d postgres -c "CREATE DATABASE $POSTGRES_DB;" 2>/dev/null || echo "Database already exists"

# Connect to the new database and create extensions
echo "🔌 Installing pgvector extension..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "CREATE EXTENSION IF NOT EXISTS vector;" || echo "pgvector extension already exists"

# Create schema
echo "📋 Creating database schema..."

PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB <<EOF

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
  id VARCHAR(255) PRIMARY KEY,
  filename VARCHAR(500) NOT NULL,
  file_path VARCHAR(1000) NOT NULL,
  total_chunks INTEGER DEFAULT 0,
  embedding_model VARCHAR(255) DEFAULT 'openai/text-embedding-3-small',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ingested BOOLEAN DEFAULT FALSE
);

-- Chunks table with pgvector embeddings
CREATE TABLE IF NOT EXISTS chunks (
  id VARCHAR(255) PRIMARY KEY,
  document_id VARCHAR(255) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  page_number INTEGER,
  chunk_index INTEGER,
  embedding vector(1536),  -- Dimensions for text-embedding-3-small
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for fast similarity search
CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Conversation history table
CREATE TABLE IF NOT EXISTS conversation_history (
  id VARCHAR(255) PRIMARY KEY,
  session_id VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL,  -- 'user' or 'assistant'
  content TEXT NOT NULL,
  citations TEXT,  -- JSON string
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS conversation_session_idx ON conversation_history(session_id);

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_logs (
  id SERIAL PRIMARY KEY,
  event_type VARCHAR(50) NOT NULL,  -- 'document_uploaded', 'query_made', etc.
  details TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $POSTGRES_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $POSTGRES_USER;

EOF

echo "✅ Database schema created successfully!"

# Show table information
echo ""
echo "📊 Database Schema Summary:"
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
"

echo ""
echo "✨ PostgreSQL initialization complete!"
echo ""
echo "📝 Connection String:"
echo "postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB"
echo ""
