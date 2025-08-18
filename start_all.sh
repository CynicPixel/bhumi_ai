#!/bin/bash

# Bhumi AI - Start All Services Script
# This script starts the agricultural orchestrator and all specialized agents

echo "🌾 Starting Bhumi AI Agricultural Intelligence System..."
echo "=================================================="

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $1 is already in use"
        return 1
    else
        return 0
    fi
}

# Function to start an agent
start_agent() {
    local agent_name=$1
    local agent_path=$2
    local port=$3
    
    echo "🚀 Starting $agent_name on port $port..."
    
    if check_port $port; then
        if [ -d "$agent_path" ]; then
            cd "$agent_path"
            python __main__.py --port $port &
            echo "✅ $agent_name started (PID: $!)"
            cd - > /dev/null  # Return to original directory
            sleep 2
        else
            echo "❌ Directory $agent_path not found"
        fi
    else
        echo "❌ Cannot start $agent_name - port $port is busy"
    fi
}

# Start the specialized agents first
echo ""
echo "📋 Starting Specialized Agents..."
echo "----------------------------------"

# Start Schemes RAG Agent (Port 10004)
start_agent "Schemes RAG Agent" "schemes_rag_agent" 10004

# Start Weather Agent (Port 10005)  
start_agent "Weather Agent" "weather_agent_adk" 10005

# Start Market Agent (Port 10006)
start_agent "Market Intelligence Agent" "market_agent_adk" 10006

echo ""
echo "🎯 Starting Orchestrator..."
echo "----------------------------"

# Start Agricultural Orchestrator (Port 10007)
start_agent "Agricultural Orchestrator" "agricultural_orchestrator" 10007

echo ""
echo "🌐 Starting Frontend..."
echo "------------------------"

# Start Frontend (Port 3000)
if check_port 3000; then
    echo "🚀 Starting Frontend on port 3000..."
    if [ -d "frontend" ]; then
        cd frontend
        npm run dev &
        echo "✅ Frontend started (PID: $!)"
        cd - > /dev/null  # Return to original directory
    else
        echo "❌ Frontend directory not found"
    fi
else
    echo "❌ Cannot start Frontend - port 3000 is busy"
fi

echo ""
echo "=================================================="
echo "🎉 Bhumi AI System Started Successfully!"
echo ""
echo "📍 Service URLs:"
echo "   • Frontend:        http://localhost:3000"
echo "   • Orchestrator:    http://localhost:10007"
echo "   • Market Agent:    http://localhost:10006"
echo "   • Weather Agent:   http://localhost:10005"
echo "   • Schemes Agent:   http://localhost:10004"
echo ""
echo "📋 Health Check URLs:"
echo "   • Orchestrator:    http://localhost:10007/.well-known/agent.json"
echo "   • Market Agent:    http://localhost:10006/.well-known/agent.json"
echo "   • Weather Agent:   http://localhost:10005/.well-known/agent.json"
echo "   • Schemes Agent:   http://localhost:10004/.well-known/agent.json"
echo ""
echo "💡 Tips:"
echo "   • Wait 30-60 seconds for all services to fully initialize"
echo "   • Check individual agent logs if any service fails to start"
echo "   • Use Ctrl+C to stop all services"
echo "   • Run './stop_all.sh' to gracefully stop all services"
echo ""
echo "🌾 Happy Farming with AI! 🚀"

# Wait for user input to keep script running
echo ""
echo "Press Ctrl+C to stop all services..."
wait
