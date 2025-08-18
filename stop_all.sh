#!/bin/bash

# Bhumi AI - Stop All Services Script
# This script gracefully stops all running Bhumi AI services

echo "🛑 Stopping Bhumi AI Agricultural Intelligence System..."
echo "======================================================="

# Function to stop processes on a specific port
stop_port() {
    local port=$1
    local service_name=$2
    
    echo "🔍 Checking for $service_name on port $port..."
    
    local pids=$(lsof -ti:$port)
    if [ -n "$pids" ]; then
        echo "🛑 Stopping $service_name (PIDs: $pids)..."
        kill $pids
        sleep 2
        
        # Force kill if still running
        local remaining_pids=$(lsof -ti:$port)
        if [ -n "$remaining_pids" ]; then
            echo "⚠️  Force stopping $service_name (PIDs: $remaining_pids)..."
            kill -9 $remaining_pids
        fi
        
        echo "✅ $service_name stopped"
    else
        echo "ℹ️  No $service_name process found on port $port"
    fi
}

# Stop all services
echo ""
echo "🛑 Stopping All Services..."
echo "---------------------------"

# Stop Frontend (Port 3000)
stop_port 3000 "Frontend"

# Stop Agricultural Orchestrator (Port 10007)
stop_port 10007 "Agricultural Orchestrator"

# Stop Market Agent (Port 10006)
stop_port 10006 "Market Intelligence Agent"

# Stop Weather Agent (Port 10005)
stop_port 10005 "Weather Agent"

# Stop Schemes Agent (Port 10004)
stop_port 10004 "Schemes RAG Agent"

# Also stop any remaining Python processes that might be related
echo ""
echo "🧹 Cleaning up remaining processes..."
echo "------------------------------------"

# Find and stop any remaining bhumi_ai related processes
remaining_processes=$(ps aux | grep -E "(agricultural_orchestrator|market_agent|weather_agent|schemes_rag|bhumi)" | grep -v grep | awk '{print $2}')

if [ -n "$remaining_processes" ]; then
    echo "🔍 Found remaining Bhumi AI processes: $remaining_processes"
    echo "🛑 Stopping remaining processes..."
    kill $remaining_processes 2>/dev/null
    sleep 2
    
    # Force kill any stubborn processes
    still_running=$(ps aux | grep -E "(agricultural_orchestrator|market_agent|weather_agent|schemes_rag|bhumi)" | grep -v grep | awk '{print $2}')
    if [ -n "$still_running" ]; then
        echo "⚠️  Force stopping stubborn processes: $still_running"
        kill -9 $still_running 2>/dev/null
    fi
    
    echo "✅ Cleanup completed"
else
    echo "ℹ️  No remaining Bhumi AI processes found"
fi

echo ""
echo "======================================================="
echo "✅ Bhumi AI System Stopped Successfully!"
echo ""
echo "📋 Verification:"
echo "   • All ports should now be free"
echo "   • No Bhumi AI processes should be running"
echo ""
echo "💡 To restart the system, run: ./start_all.sh"
echo ""
echo "🌾 Thank you for using Bhumi AI! 👋"
