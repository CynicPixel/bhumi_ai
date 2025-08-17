#!/bin/bash

# Agricultural Intelligence Orchestrator Runner Script

echo "🌾 Starting Agricultural Intelligence Orchestrator..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please copy env.example to .env and configure your settings:"
    echo "cp env.example .env"
    echo "Then edit .env with your GOOGLE_API_KEY and agent URLs"
    exit 1
fi

# Check if GOOGLE_API_KEY is set
if ! grep -q "GOOGLE_API_KEY=" .env || grep -q "GOOGLE_API_KEY=your_google_api_key_here" .env; then
    echo "❌ GOOGLE_API_KEY not properly configured in .env file!"
    echo "Please set your actual Google API key in the .env file"
    exit 1
fi

# Check if required agents are configured
if ! grep -q "MARKET_AGENT_URL=" .env || ! grep -q "WEATHER_AGENT_URL=" .env; then
    echo "❌ Agent URLs not configured in .env file!"
    echo "Please configure MARKET_AGENT_URL and WEATHER_AGENT_URL"
    exit 1
fi

echo "✅ Environment configuration verified"
echo "🚀 Starting orchestrator server..."

# Run the orchestrator
python -m agricultural_orchestrator --host localhost --port 10007
