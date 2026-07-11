#!/bin/bash

# HR Agent Bot - Quick Start Script
# Automates setup for local development

set -e

echo "🚀 HR Agent Bot - Quick Start Setup"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
check_prerequisites() {
    echo -e "${BLUE}📋 Checking prerequisites...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker not found. Please install Docker Desktop."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose not found. Please install Docker Compose."
        exit 1
    fi
    
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js not found. Please install Node.js 18+"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python not found. Please install Python 3.10+"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All prerequisites installed${NC}"
    echo ""
}

# Get OpenRouter API key
get_openrouter_key() {
    echo -e "${BLUE}🔑 OpenRouter API Key${NC}"
    echo "Need OpenRouter API key for LLM access."
    echo "Get free key at: https://openrouter.ai"
    echo ""
    
    read -p "Enter your OpenRouter API key (sk-or-v1-...): " OPENROUTER_API_KEY
    
    if [ -z "$OPENROUTER_API_KEY" ]; then
        echo "❌ API key is required!"
        exit 1
    fi
    
    export OPENROUTER_API_KEY
    echo -e "${GREEN}✅ API key saved${NC}"
    echo ""
}

# Setup backend
setup_backend() {
    echo -e "${BLUE}⚙️  Setting up Backend...${NC}"
    
    cd backend
    
    # Create .env file
    cat > .env <<EOF
OPENROUTER_API_KEY=$OPENROUTER_API_KEY
OPENROUTER_LLM_MODEL=anthropic/claude-3-5-sonnet
OPENROUTER_EMBED_MODEL=openai/text-embedding-3-small

DATABASE_URL=postgresql://admin:secure_password@localhost:5433/hr_agent

CHUNK_SIZE=512
CHUNK_OVERLAP=64
TOP_K_RETRIEVAL=5
SIMILARITY_THRESHOLD=0.7

DEBUG=true
WORKERS=4
PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
EOF
    
    echo -e "${GREEN}✅ Backend .env created${NC}"
    cd ..
}

# Setup frontend
setup_frontend() {
    echo -e "${BLUE}⚙️  Setting up Frontend...${NC}"
    
    cd frontend
    
    # Create .env.local file
    cat > .env.local <<EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=HR Agent Bot
EOF
    
    # Install dependencies
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing npm dependencies..."
        npm install
    fi
    
    echo -e "${GREEN}✅ Frontend setup complete${NC}"
    cd ..
}

# Start services
start_services() {
    echo -e "${BLUE}🐳 Starting Docker services...${NC}"
    
    cd docker
    docker-compose up -d
    cd ..
    
    echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
    sleep 10
    
    echo -e "${GREEN}✅ Docker services started${NC}"
    echo ""
}

# Start backend
start_backend() {
    echo -e "${BLUE}🚀 Starting Backend Server...${NC}"
    echo "Running on http://localhost:8000"
    echo "API Docs: http://localhost:8000/docs"
    echo ""
    
    cd backend
    uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ..
}

# Start frontend
start_frontend() {
    echo -e "${BLUE}🚀 Starting Frontend Server...${NC}"
    echo "Running on http://localhost:3000"
    echo ""
    
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
}

# Main flow
main() {
    check_prerequisites
    
    # Ask if user wants automatic setup
    read -p "Do you want automatic setup? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        get_openrouter_key
        setup_backend
        setup_frontend
        start_services
        
        echo ""
        echo -e "${GREEN}═════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}✨ Setup Complete!${NC}"
        echo -e "${GREEN}═════════════════════════════════════════════════${NC}"
        echo ""
        echo "📖 Next Steps:"
        echo ""
        echo "1️⃣  Terminal 1 - Start Backend:"
        echo "   cd backend && uvicorn main:app --reload"
        echo ""
        echo "2️⃣  Terminal 2 - Start Frontend:"
        echo "   cd frontend && npm run dev"
        echo ""
        echo "3️⃣  Open Browser:"
        echo "   Frontend: http://localhost:3000"
        echo "   API Docs: http://localhost:8000/docs"
        echo "   PgAdmin:  http://localhost:5050"
        echo ""
        echo "4️⃣  Default Credentials:"
        echo "   PostgreSQL: admin / secure_password"
        echo "   PgAdmin:    admin@hragent.local / pgadmin_password"
        echo ""
        echo "5️⃣  Upload HR Policies:"
        echo "   - Go to http://localhost:3000/admin/documents"
        echo "   - Drag & drop PDF files"
        echo "   - System will automatically ingest and index"
        echo ""
        echo "6️⃣  Try a Question:"
        echo "   - Go to http://localhost:3000"
        echo "   - Ask: 'What is my notice period?'"
        echo ""
        echo -e "${YELLOW}📝 Remember:${NC}"
        echo "   - Keep Docker running: docker-compose -f docker/docker-compose.yml up -d"
        echo "   - Stop services: docker-compose -f docker/docker-compose.yml down"
        echo "   - View logs: docker-compose -f docker/docker-compose.yml logs -f backend"
        echo ""
    else
        echo "Manual setup mode. Run these commands in separate terminals:"
        echo ""
        echo "Terminal 1 (Database):"
        echo "  docker-compose -f docker/docker-compose.yml up -d"
        echo ""
        echo "Terminal 2 (Backend):"
        echo "  cd backend && uvicorn main:app --reload"
        echo ""
        echo "Terminal 3 (Frontend):"
        echo "  cd frontend && npm run dev"
        echo ""
    fi
}

# Handle cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down services...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    cd docker && docker-compose down 2>/dev/null || true
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

trap cleanup EXIT

main

# Keep script running
wait
