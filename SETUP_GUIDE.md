# 🌾 Bhumi AI - Complete Setup Guide

This guide will help you set up and run the complete Bhumi AI Agricultural Intelligence System with the new multimodal frontend.

## 📋 System Overview

**Architecture:**
```
Frontend (Next.js) → Orchestrator Agent → Specialized Agents
    Port 3000           Port 10007      ├── Market Agent (10006)
                                       ├── Weather Agent (10005)
                                       └── Schemes Agent (10004)
```

**Key Features:**
- 🌾 **Multimodal Input**: Text, voice, and image support
- 📊 **Market Intelligence**: Real-time commodity prices
- 🌤️ **Weather Insights**: Agricultural forecasts
- 📋 **Government Schemes**: RAG-powered subsidies database
- 🤖 **Intelligent Routing**: Smart agent coordination

## 🚀 Quick Start (Recommended)

### Prerequisites
- Python 3.11+
- Node.js 18+
- Required API keys (see Environment Setup)

### 1. Clone and Setup
```bash
# Navigate to the project directory
cd bhumi_ai

# Make scripts executable (if not already done)
chmod +x start_all.sh stop_all.sh
```

### 2. Environment Setup
Set up environment variables for all agents:

**Agricultural Orchestrator (.env):**
```env
GOOGLE_API_KEY=your_google_api_key_here
MARKET_AGENT_URL=http://localhost:10006
WEATHER_AGENT_URL=http://localhost:10005
HOST=localhost
PORT=10007
```

**Market Agent (.env):**
```env
CEDA_API_KEY=your_ceda_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

**Weather Agent (.env):**
```env
GOOGLE_API_KEY=your_google_api_key_here
```

**Schemes RAG Agent (.env):**
```env
GOOGLE_API_KEY=your_google_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=your_index_name
```

**Frontend (.env.local):**
```env
NEXT_PUBLIC_ORCHESTRATOR_URL=http://localhost:10007
NEXT_PUBLIC_ENABLE_AUDIO=true
NEXT_PUBLIC_ENABLE_IMAGE_UPLOAD=true
```

### 3. Install Dependencies

**Backend Dependencies:**
```bash
# Install Python dependencies for each agent
cd agricultural_orchestrator && pip install -r requirements.txt && cd ..
cd market_agent_adk && pip install -e . && cd ..
cd weather_agent_adk && pip install -e . && cd ..
cd schemes_rag_agent && pip install -r requirements.txt && cd ..
```

**Frontend Dependencies:**
```bash
cd frontend
npm install
cd ..
```

### 4. Start All Services
```bash
# Start everything with one command
./start_all.sh
```

### 5. Access the Application
- **Frontend**: http://localhost:3000
- **Orchestrator**: http://localhost:10007
- **Health Checks**: See URLs in terminal output

## 🔧 Manual Setup (Advanced)

If you prefer to start services individually:

### 1. Start Backend Agents
```bash
# Terminal 1 - Schemes Agent
cd schemes_rag_agent
python __main__.py --port 10004

# Terminal 2 - Weather Agent  
cd weather_agent_adk
python __main__.py --port 10005

# Terminal 3 - Market Agent
cd market_agent_adk
python __main__.py --port 10006

# Terminal 4 - Orchestrator
cd agricultural_orchestrator
python __main__.py --port 10007
```

### 2. Start Frontend
```bash
# Terminal 5 - Frontend
cd frontend
npm run dev
```

## 🧪 Testing the System

### 1. Health Check
Visit these URLs to verify all services are running:
- http://localhost:10007/.well-known/agent.json (Orchestrator)
- http://localhost:10006/.well-known/agent.json (Market Agent)
- http://localhost:10005/.well-known/agent.json (Weather Agent)
- http://localhost:10004/.well-known/agent.json (Schemes Agent)

### 2. Frontend Testing
1. Open http://localhost:3000
2. Try these test queries:

**Text Input:**
- "What are onion prices in Mumbai today?"
- "Weather forecast for farming in Punjab"
- "Government schemes for organic farming"

**Voice Input:**
- Click the microphone icon
- Record a farming question
- Send and verify response

**Image Input:**
- Click the paperclip icon
- Upload a crop/field image
- Add description and send

### 3. Backend API Testing
```bash
# Test orchestrator directly
curl -X POST http://localhost:10007/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test_001",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"type": "text", "text": "user_id: farmer_test\n\nWhat are potato prices in Delhi?"}],
        "messageId": "msg_001"
      }
    }
  }'
```

## 🛑 Stopping the System

### Quick Stop
```bash
./stop_all.sh
```

### Manual Stop
Press `Ctrl+C` in each terminal window running the services.

## 🔑 API Keys Required

### Google API Key
1. Visit [Google AI Studio](https://ai.google.dev/)
2. Create a new API key
3. Add to all agent `.env` files as `GOOGLE_API_KEY`

### CEDA API Key (Market Agent)
1. Register at [CEDA Agmarknet](https://agmarknet.gov.in/)
2. Get API access credentials
3. Add as `CEDA_API_KEY` in market agent `.env`

### Pinecone API Key (Schemes Agent)
1. Sign up at [Pinecone](https://www.pinecone.io/)
2. Create a new index for agricultural schemes
3. Add credentials to schemes agent `.env`

## 📱 Frontend Features

### Multimodal Input
- **Text**: Natural language queries with auto-complete
- **Voice**: Audio recording with waveform visualization
- **Images**: Drag & drop or camera capture for analysis

### UI Components
- **Chat Interface**: Modern message bubbles with timestamps
- **Connection Status**: Real-time backend connectivity monitoring
- **Quick Actions**: Pre-defined buttons for common queries
- **Settings Panel**: User ID and backend configuration

### Mobile Support
- **Responsive Design**: Works on all screen sizes
- **Touch Interactions**: Mobile-optimized controls
- **Camera Access**: Direct photo capture on mobile devices
- **Microphone Access**: Voice recording with permissions

## 🐛 Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Check what's using a port
lsof -i :10007

# Kill process on port
kill $(lsof -ti:10007)
```

**Frontend Not Connecting:**
- Verify `NEXT_PUBLIC_ORCHESTRATOR_URL` in `.env.local`
- Check orchestrator is running on correct port
- Ensure CORS is configured properly

**Voice Recording Not Working:**
- Grant microphone permissions in browser
- Use HTTPS in production
- Check browser compatibility (Chrome/Firefox recommended)

**Image Upload Issues:**
- Verify file size limits (5MB default)
- Check supported formats: PNG, JPG, WebP, GIF
- Ensure proper MIME type handling

**Agent Connection Failures:**
- Verify all environment variables are set
- Check API key validity and quotas
- Review agent logs for specific error messages

### Debug Mode
Enable debug logging in agents:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Log Locations
- **Frontend**: Browser console (F12)
- **Agents**: Terminal output where each agent is running
- **Orchestrator**: Terminal output with detailed routing logs

## 🔒 Security Considerations

### Development
- Use HTTP for local development
- Keep API keys in `.env` files (not committed to git)
- Grant microphone/camera permissions as needed

### Production
- Use HTTPS for all services
- Implement proper CORS policies
- Use environment-specific API keys
- Consider rate limiting and authentication

## 📊 Performance Tips

### Backend Optimization
- Use appropriate timeout values for agent calls
- Implement connection pooling for database connections
- Monitor memory usage with multiple concurrent users

### Frontend Optimization
- Enable image compression for uploads
- Implement message pagination for long conversations
- Use service workers for offline functionality

## 🤝 Contributing

### Development Workflow
1. Make changes to individual components
2. Test with `npm run dev` (frontend) and `python __main__.py` (agents)
3. Verify multimodal features work correctly
4. Test backend integration thoroughly
5. Update documentation as needed

### Code Structure
- **Frontend**: `/frontend/src/` - React components and utilities
- **Backend**: Individual agent directories with `__main__.py` entry points
- **Shared**: Common utilities and type definitions

## 📞 Support

### Getting Help
1. Check this setup guide first
2. Review individual agent README files
3. Check browser console for frontend errors
4. Review agent terminal output for backend errors
5. Verify all environment variables are correctly set

### Common Resources
- [Next.js Documentation](https://nextjs.org/docs)
- [A2A Framework](https://github.com/google/agent-to-agent)
- [Google AI Studio](https://ai.google.dev/)
- [Tailwind CSS](https://tailwindcss.com/docs)

---

## 🎉 Success!

If everything is working correctly, you should see:
- ✅ All 4 backend agents running and healthy
- ✅ Frontend accessible at http://localhost:3000
- ✅ Multimodal input (text, voice, image) working
- ✅ Real-time responses from agricultural intelligence system
- ✅ Connection status monitoring and error handling

**🌾 You're now ready to use Bhumi AI for intelligent agricultural assistance! 🚀**
