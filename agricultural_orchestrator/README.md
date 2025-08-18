# 🌾 Agricultural Intelligence Orchestrator

A comprehensive MVP orchestrator agent that provides intelligent agricultural support for Indian farmers by coordinating specialized market and weather agents.

## 🎯 Overview

The Agricultural Intelligence Orchestrator is an intelligent coordinator that:
- **Orchestrates** specialized market and weather agents
- **Combines** market intelligence with weather forecasts
- **Provides** holistic farming advice for Indian agriculture
- **Supports** natural language queries in farmer-friendly language

## 🏗️ Architecture

```
User Query → Orchestrator Agent → Route to Specialized Agents → Collect & Synthesize → Present Unified Response
                                    ↓
                            Market Agent (Port 10006)
                            Weather Agent (Port 10005)
```

## 🚀 Features

### Core Capabilities
- **Market + Weather Intelligence**: Combine commodity prices with weather forecasts
- **Farming Conditions Analysis**: Analyze current farming conditions using multiple data sources
- **Seasonal Agricultural Planning**: Provide seasonal advice for different crops and regions
- **Regional Farming Comparison**: Compare conditions across different Indian states
- **Intelligent Agent Orchestration**: Coordinate multiple specialized agents

### Agricultural Tools
- `get_market_weather_insights`: Combined market and weather analysis
- `analyze_farming_conditions`: Comprehensive farming condition assessment
- `get_seasonal_advice`: Seasonal planning with market and weather data
- `compare_regional_conditions`: Cross-regional farming analysis

## 📋 Prerequisites

- Python 3.11+
- Google API Key for Gemini models
- Running Market Agent (Port 10006)
- Running Weather Agent (Port 10005)

## 🛠️ Installation

1. **Clone and navigate to the project:**
```bash
cd agricultural_orchestrator
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
```bash
cp env.example .env
# Edit .env with your configuration
```

4. **Configure your .env file:**
```env
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_MODEL_NAME=gemini-2.0-flash-exp

# Agent URLs (update these to match your running agents)
MARKET_AGENT_URL=http://localhost:10006
WEATHER_AGENT_URL=http://localhost:10005

# Server Configuration
HOST=localhost
PORT=10007

# Timeout Configuration
AGENT_TIMEOUT=30
SYNTHESIS_TIMEOUT=60
```

## 🚀 Running the Orchestrator

### Start the Orchestrator Server
```bash
python -m agricultural_orchestrator --host localhost --port 10007
```

### Alternative: Direct execution
```bash
python agricultural_orchestrator/__main__.py --host localhost --port 10007
```

## 🧪 Testing

### Test the Complete Orchestrator
```bash
python agricultural_orchestrator/test_client.py
```

### Test Specific Capabilities
```bash
# Test market + weather insights
python agricultural_orchestrator/test_client.py market_weather

# Test farming conditions analysis
python agricultural_orchestrator/test_client.py farming_conditions

# Test seasonal planning
python agricultural_orchestrator/test_client.py seasonal

# Test regional comparison
python agricultural_orchestrator/test_client.py regional
```

## 💬 Example Queries

### Market + Weather Intelligence
```
"What are the current onion prices in Mumbai and how will the weather affect farming?"
"Get potato prices in Delhi today along with weather forecast for farming decisions"
"Show rice prices in Punjab this week with weather conditions for planting"
```

### Farming Conditions Analysis
```
"Analyze farming conditions for wheat in Haryana"
"What are the current conditions for tomato farming in Maharashtra?"
"Assess farming conditions for cotton in Gujarat"
```

### Seasonal Planning
```
"Plan my crop rotation for the next 6 months in Bihar"
"When should I start preparing for monsoon crops in Kerala?"
"Best crops to plant in Rajasthan this season considering market and weather"
```

### Regional Comparison
```
"Compare farming conditions for tomatoes across Maharashtra and Karnataka"
"Which region is better for wheat farming: Punjab or Haryana?"
"Compare rice farming conditions in West Bengal vs Tamil Nadu"
```

## 🔧 Configuration

### Port Configuration
- **Orchestrator Agent**: Port 10007
- **Market Agent**: Port 10006 (existing)
- **Weather Agent**: Port 10005 (existing)

### Environment Variables
- `GOOGLE_API_KEY`: Required for Gemini model access
- `GOOGLE_MODEL_NAME`: Gemini model to use (default: gemini-2.0-flash-exp)
- `MARKET_AGENT_URL`: URL of the Market Intelligence Agent
- `WEATHER_AGENT_URL`: URL of the Weather Agent
- `HOST`: Host to bind the server to
- `PORT`: Port for the orchestrator server

## 📁 Project Structure

```
agricultural_orchestrator/
├── __init__.py                 # Package initialization
├── __main__.py                 # A2A server setup and entry point
├── agent.py                    # Core orchestrator logic with ADK
├── agent_executor.py           # A2A framework bridge
├── remote_agent_manager.py     # Manages connections to specialized agents
├── agricultural_tools.py       # Domain-specific orchestration tools
├── test_client.py              # Test client for demonstration
├── pyproject.toml             # Dependencies and project configuration
├── env.example                # Environment variables template
└── README.md                  # This file
```

## 🔄 How It Works

1. **Query Reception**: User sends natural language agricultural query
2. **Intent Analysis**: Orchestrator analyzes query to determine required agents
3. **Agent Coordination**: Queries relevant specialized agents concurrently
4. **Response Collection**: Gathers responses from market and weather agents
5. **Synthesis**: Combines responses into coherent agricultural advice
6. **Delivery**: Presents unified, actionable farming recommendations

## 📤 Message Format to Specialized Agents

When the orchestrator communicates with your specialized agents, it sends messages in this format:

```json
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "unique_id",
      "role": "user",
      "parts": [{"text": "Your query here"}],
      "metadata": {
        "user_id": "orchestrator_user",
        "session_id": "session_id"
      }
    }
  },
  "id": "request_id"
}
```

This ensures compatibility with your existing Market and Weather agents.

## 🌟 Key Benefits

- **Comprehensive Insights**: Combines market and weather data for holistic analysis
- **Farmer-Friendly**: Provides practical, actionable advice in clear language
- **Intelligent Routing**: Automatically determines which agents to involve
- **Real-Time Data**: Leverages live market and weather information
- **Regional Context**: Tailored advice for Indian agricultural regions
- **Scalable Architecture**: Easy to add new specialized agents

## 🚨 Troubleshooting

### Common Issues

1. **"No agents available"**
   - Ensure Market and Weather agents are running
   - Check agent URLs in .env file
   - Verify agent ports are accessible

2. **"GOOGLE_API_KEY not set"**
   - Set GOOGLE_API_KEY in your .env file
   - Get API key from [Google AI Studio](https://ai.google.dev/)

3. **Connection timeouts**
   - Check if specialized agents are responding
   - Verify network connectivity
   - Adjust timeout values in .env if needed

### Debug Mode
Enable debug logging by modifying the logging level in the code:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 🔗 API Endpoints

The orchestrator exposes standard A2A endpoints:
- `/.well-known/agent.json`: Agent capabilities and metadata
- `/message/send`: Send messages to the orchestrator
- `/tasks/{task_id}`: Task status and updates

## 📚 Dependencies

- **a2a-python**: Agent-to-Agent framework
- **google-adk**: Google Agent Development Kit
- **google-generativeai**: Gemini AI models
- **httpx**: Async HTTP client
- **uvicorn**: ASGI server
- **python-dotenv**: Environment variable management

## 🤝 Contributing

This is an MVP implementation. Future enhancements could include:
- Agent load balancing
- Response caching
- Learning orchestration patterns
- Multi-modal support
- Regional specialization

## 📄 License

This project is part of the Agricultural AI initiative for Indian farmers.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Verify all agents are running
3. Check environment configuration
4. Review server logs for error details

---

**🌾 Built for Indian Farmers - Intelligent Agricultural Support Through AI Orchestration**

## 📋 **JSON Schema for Queries**

### **Request Schema (POST to /)**

```json
{
  "jsonrpc": "2.0",
  "id": "unique_request_id",
  "method": "message/stream",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "text",
          "text": "What are the current onion prices in Mumbai and how will the weather affect farming?"
        }
      ],
      "messageId": "unique_message_id"
    }
  }
}
```

### **Simplified Request Schema (Alternative)**

```json
{
  "jsonrpc": "2.0",
  "id": "test_001",
  "method": "message/stream",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "text",
          "text": "Analyze farming conditions for wheat in Haryana"
        }
      ],
      "messageId": "msg_001"
    }
  }
}
```
