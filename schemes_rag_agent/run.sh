#!/bin/bash

# Schemes RAG Agent Startup Script

echo "🚀 Starting Schemes RAG Agent API Server..."
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "✅ Created .env file from template. Please edit it with your API keys."
        echo "   Press Enter to continue or Ctrl+C to edit .env first..."
        read
    else
        echo "❌ env.example not found. Please create .env file manually."
        exit 1
    fi
fi

# Create logs directory
echo "📁 Creating logs directory..."
mkdir -p logs

# Check if port is in use and kill if necessary
PORT=8000
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port $PORT is in use. Attempting to kill existing process..."
    PID=$(lsof -ti:$PORT)
    if [ ! -z "$PID" ]; then
        kill -9 $PID
        echo "✅ Killed process using port $PORT"
        sleep 2
    fi
fi

echo "🧪 Testing setup..."
python3 -c "
from main import app
from config import Config
from logging_config import setup_logging
setup_logging()
print('✅ Setup test passed!')
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Setup test passed! Starting server..."
    echo "🌐 Server will be available at: http://localhost:$PORT"
    echo "📚 API Documentation: http://localhost:$PORT/docs"
    echo "📁 Logs will be stored in: ./logs/"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo ""
    
    # Start the server
    python3 start_server.py
else
    echo ""
    echo "❌ Setup test failed. Please check the errors above."
    echo "Common solutions:"
    echo "1. Verify your API keys in .env file"
    echo "2. Check if MongoDB and Pinecone are accessible"
    echo "3. Ensure all dependencies are installed"
    exit 1
fi
