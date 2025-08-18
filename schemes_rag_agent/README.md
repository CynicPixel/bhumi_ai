# Agricultural Schemes Intelligence Agent

A powerful AI-powered agricultural schemes assistant that uses Retrieval-Augmented Generation (RAG) to provide accurate, context-aware responses about government agricultural programs and schemes for Indian farmers. Now integrated with A2A (Agent-to-Agent) protocol for seamless multi-agent orchestration.

## 🚀 Features

### 🎯 **7 Advanced Agricultural Schemes Intelligence Skills**

1. **Advanced Agricultural Scheme Discovery & Analysis**: Intelligent discovery across 453+ scheme documents and government programs
2. **Comprehensive Eligibility Analysis & Application Guidance**: Step-by-step application guidance with personalized recommendations  
3. **Context-Aware Scheme Intelligence & Conversation Continuity**: MongoDB persistence for personalized recommendations and continuous dialogue
4. **Advanced Subsidy & Benefits Analysis**: Comprehensive subsidy calculation and financial impact assessment
5. **Specialized Farmer Support & Category-Specific Assistance**: Targeted support for women, tribal, small/marginal farmers
6. **Real-Time Scheme Updates & Latest Information**: Access to latest updates, new launches, and policy changes
7. **Advanced RAG Orchestration & Intelligent Document Retrieval**: Sophisticated Pinecone vector search and context-aware synthesis

### Core RAG Capabilities
- **RAG-Powered Responses**: Uses Pinecone vector database to retrieve relevant agricultural scheme information
- **Conversation Memory**: Stores and retrieves conversation history using MongoDB
- **Gemini AI Integration**: Powered by Google's Gemini 2.0 Flash model
- **Real-time Context**: Provides relevant information based on user queries
- **Session Management**: Maintains conversation context across multiple interactions

### A2A Integration
- **Multi-Agent Orchestration**: Seamlessly integrates with Agricultural Orchestrator
- **Protocol Compliance**: Full A2A (Agent-to-Agent) protocol support
- **Streaming Responses**: Real-time status updates via A2A events
- **Discovery**: Automatic agent discovery via agent cards
- **Context Preservation**: Maintains conversation context across A2A sessions

### Dual Interface Support
- **A2A Protocol**: For multi-agent integration (Port 10007)
- **REST API**: For standalone applications (Port 8010)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                A2A Protocol Layer                           │
├─────────────────────────────────────────────────────────────┤
│ A2AStarletteApplication                                     │
│ ├── AgentCard (/.well-known/agent.json)                   │
│ ├── CustomRequestHandler                                   │
│ └── JSON-RPC 2.0 Endpoints (/a2a)                         │
├─────────────────────────────────────────────────────────────┤
│                Agent Executor Layer                         │
├─────────────────────────────────────────────────────────────┤
│ SchemesAgentExecutor (A2A ↔ RAG Bridge)                   │
│ ├── A2A RequestContext → RAG Query Translation             │
│ ├── Event-Driven Status Updates                            │
│ ├── Streaming Response Handling                            │
│ └── A2A Task Lifecycle Management                          │
├─────────────────────────────────────────────────────────────┤
│            Core RAG Engine (Preserved)                     │
├─────────────────────────────────────────────────────────────┤
│ SchemesRAGAgent                                            │
│ ├── Gemini 2.0 Flash Integration                          │
│ ├── Pinecone Vector Search                                 │
│ ├── MongoDB Conversation History                           │
│ ├── Unified RAG Context Building                           │
│ └── Response Generation                                     │
└─────────────────────────────────────────────────────────────┘
```

## � Quick Start

### A2A Mode (Recommended for Multi-Agent Integration)

1. **Start the A2A server:**
   ```bash
   python __main__.py
   ```
   
   Server will start on `http://localhost:10007` with A2A protocol support.

2. **Test with A2A client:**
   ```bash
   python simple_query.py "What schemes are available for organic farming?"
   ```

3. **Interactive A2A testing:**
   ```bash
   python simple_query.py interactive
   ```

### Standalone Mode (Legacy REST API)

1. **Start the FastAPI server:**
   ```bash
   python main.py
   ```
   
   Server will start on `http://localhost:8010` with REST API.

2. **Access the API documentation:**
   - Swagger UI: `http://localhost:8010/docs`
   - ReDoc: `http://localhost:8010/redoc`

## 🛠️ Installation

1. **Clone the repository and navigate to the directory:**
   ```bash
   cd bhumi_ai/schemes_rag_agent
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your actual API keys and configuration
   ```

4. **Verify your configuration:**
   - Google AI API key is valid
   - MongoDB connection string is accessible
   - Pinecone API key and index are configured

## ⚙️ Configuration

The application uses the following environment variables:

### Required Variables
- `GOOGLE_API_KEY`: Your Google AI API key
- `MONGO_URL`: MongoDB connection string
- `PINECONE_API`: Pinecone API key
- `PINECONE_INDEX`: Pinecone index name

### A2A Configuration
- `SCHEMES_AGENT_HOST`: A2A server host (default: localhost)
- `SCHEMES_AGENT_PORT`: A2A server port (default: 10007)
- `A2A_AGENT_NAME`: Agent name for A2A discovery
- `A2A_STREAMING_ENABLED`: Enable streaming responses (default: true)

### Optional Variables
- `DB_NAME`: MongoDB database name (default: Capone)
- `COLLECTION_NAME`: MongoDB collection name (default: Bhumi)
- `HOST`: Legacy REST API host (default: 0.0.0.0)
- `PORT`: Legacy REST API port (default: 8010)
- `DEBUG`: Debug mode (default: false)

## 🚀 Running the Server

### Option 1: Using the startup script
```bash
python start_server.py
```

### Option 2: Using uvicorn directly
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Using Python directly
```bash
python main.py
```

The server will start on `http://localhost:8000` (or your configured host/port).

## 📚 API Endpoints

### 1. Query Processing
**POST** `/query`
Process a user query and return an AI-generated response with RAG context.

**Request Body:**
```json
{
  "query": "What are the benefits of PM Kisan scheme?",
  "user_id": "user123",
  "session_id": "session456",
  "context_id": "optional_context",
  "task_id": "optional_task"
}
```

**Response:**
```json
{
  "success": true,
  "response": "The PM Kisan scheme provides...",
  "message_id": "uuid1",
  "ai_message_id": "uuid2",
  "rag_context_used": true,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 2. Conversation History
**GET** `/conversation/history?user_id={user_id}&session_id={session_id}&limit={limit}`

Retrieve conversation history for a specific user and session.

### 3. Start Conversation
**POST** `/conversation/start?user_id={user_id}&session_id={optional_session_id}`

Start a new conversation session.

### 4. Health Check
**GET** `/health`

Check the health status of all components.

### 5. Configuration
**GET** `/config`

Get current configuration (without sensitive information).

## 🔍 API Documentation

Once the server is running, you can access:
- **Interactive API docs**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative docs**: `http://localhost:8000/redoc` (ReDoc)

## 💡 Usage Examples

### Python Client Example
```python
import requests

# Start a conversation
response = requests.post(
    "http://localhost:8000/conversation/start",
    params={"user_id": "farmer123"}
)
session_data = response.json()
session_id = session_data["session_id"]

# Ask a question
query_response = requests.post(
    "http://localhost:8000/query",
    json={
        "query": "What are the eligibility criteria for PM Fasal Bima Yojana?",
        "user_id": "farmer123",
        "session_id": session_id
    }
)

print(query_response.json()["response"])
```

### cURL Example
```bash
# Start conversation
curl -X POST "http://localhost:8000/conversation/start?user_id=farmer123"

# Process query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the benefits of PM Kisan scheme?",
    "user_id": "farmer123",
    "session_id": "your_session_id"
  }'
```

## 🔧 Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Verify your MongoDB connection string
   - Check if your IP is whitelisted in MongoDB Atlas
   - Ensure the database and collection exist

2. **Pinecone Connection Failed**
   - Verify your Pinecone API key
   - Check if the index exists and is ready
   - Ensure you have sufficient quota

3. **Google AI API Error**
   - Verify your API key is valid
   - Check if you have sufficient quota
   - Ensure the model name is correct

4. **Import Errors**
   - Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version compatibility

### Logs
The application provides detailed logging. Check the console output for:
- Connection status
- Query processing details
- Error messages
- Performance metrics

## 🚀 Deployment

### Production Considerations
1. **Environment Variables**: Use proper environment variable management
2. **HTTPS**: Configure SSL/TLS certificates
3. **Load Balancing**: Use a reverse proxy (nginx, Apache)
4. **Monitoring**: Implement health checks and metrics
5. **Security**: Configure CORS appropriately for production

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "start_server.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Check the troubleshooting section
- Review the API documentation
- Open an issue on GitHub

## 🔮 Future Enhancements

- [ ] Multi-language support
- [ ] Advanced analytics and insights
- [ ] Integration with more agricultural databases
- [ ] Real-time weather integration
- [ ] Mobile app support
- [ ] Advanced conversation analytics
