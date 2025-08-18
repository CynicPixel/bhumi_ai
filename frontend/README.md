# 🌾 Bhumi AI Frontend

A modern, multimodal chatbot interface for the Bhumi AI agricultural intelligence system. Built with Next.js, TypeScript, and Tailwind CSS.

## 🎯 Features

### Multimodal Input Support
- **Text Input**: Natural language queries with auto-resize textarea
- **Voice Messages**: Record and send audio messages with waveform visualization
- **Image Upload**: Drag & drop or camera capture for crop/field analysis
- **Quick Actions**: Pre-defined buttons for common farming queries

### Modern UI/UX
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Real-time Chat**: Message bubbles with timestamps and status indicators
- **Connection Monitoring**: Live backend connection status with retry mechanism
- **Accessibility**: Screen reader friendly with ARIA labels
- **Smooth Animations**: Framer Motion powered transitions and loading states

### Agricultural Intelligence
- **Market Intelligence**: Real-time commodity prices and trading insights
- **Weather Forecasts**: Agricultural weather data and farming recommendations
- **Government Schemes**: RAG-powered agricultural subsidies and programs
- **Intelligent Routing**: Automatic query routing to specialized AI agents

## 🏗️ Architecture

```
Frontend (Next.js) → Orchestrator Agent (Port 10007) → Specialized Agents
                                                    ├── Market Agent (10006)
                                                    ├── Weather Agent (10005)
                                                    └── Schemes Agent (10004)
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Running Bhumi AI backend agents

### Installation

1. **Navigate to frontend directory:**
```bash
cd bhumi_ai/frontend
```

2. **Install dependencies:**
```bash
npm install
# or
yarn install
```

3. **Set up environment variables:**
```bash
cp env.example .env.local
```

4. **Configure your `.env.local`:**
```env
NEXT_PUBLIC_ORCHESTRATOR_URL=http://localhost:10007
NEXT_PUBLIC_APP_NAME="Bhumi AI - Agricultural Intelligence"
NEXT_PUBLIC_ENABLE_AUDIO=true
NEXT_PUBLIC_ENABLE_IMAGE_UPLOAD=true
NEXT_PUBLIC_ENABLE_VOICE_SYNTHESIS=true
```

5. **Start the development server:**
```bash
npm run dev
# or
yarn dev
```

6. **Open your browser:**
Navigate to [http://localhost:3000](http://localhost:3000)

## 📱 Usage

### Text Queries
- Type questions about farming, weather, market prices, or government schemes
- Use natural language: "What are onion prices in Mumbai today?"
- Press Enter or click Send to submit

### Voice Messages
- Click the microphone icon to start recording
- Speak your question clearly
- Click stop to finish recording
- Review and send or discard the recording

### Image Analysis
- Click the paperclip icon or drag & drop images
- Upload photos of crops, fields, or farming equipment
- Add optional text description
- Send for AI-powered analysis

### Quick Actions
Use pre-defined buttons for common queries:
- **Market Prices**: Current commodity pricing
- **Weather Forecast**: Agricultural weather insights  
- **Gov Schemes**: Available subsidies and programs
- **Crop Planning**: Seasonal planting recommendations

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_ORCHESTRATOR_URL` | Backend orchestrator endpoint | `http://localhost:10007` |
| `NEXT_PUBLIC_ENABLE_AUDIO` | Enable voice message features | `true` |
| `NEXT_PUBLIC_ENABLE_IMAGE_UPLOAD` | Enable image upload features | `true` |
| `NEXT_PUBLIC_ENABLE_VOICE_SYNTHESIS` | Enable text-to-speech | `true` |

### Backend Integration

The frontend communicates with the agricultural orchestrator using JSON-RPC 2.0 protocol:

**Request Format:**
```json
{
  "jsonrpc": "2.0",
  "id": "unique_request_id",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "text",
          "text": "user_id: farmer_12\n\nWhat are onion prices in Mumbai?"
        }
      ],
      "messageId": "msg_001"
    }
  }
}
```

**Response Format:**
```json
{
  "id": "unique_request_id",
  "jsonrpc": "2.0",
  "result": {
    "contextId": "context_id",
    "history": [...],
    "id": "task_id",
    "kind": "task",
    "status": {
      "message": {
        "parts": [{"kind": "text", "text": "Response text"}],
        "role": "agent"
      },
      "state": "completed"
    }
  }
}
```

## 🎨 Customization

### Styling
- Built with Tailwind CSS for easy customization
- Agricultural green color scheme with customizable primary colors
- Responsive breakpoints for all device sizes
- Custom animations and transitions

### Components
- Modular component architecture
- Reusable UI components in `/src/components/ui/`
- Chat-specific components in `/src/components/chat/`
- Easy to extend and customize

## 📱 Mobile Support

- **Responsive Design**: Optimized for mobile, tablet, and desktop
- **Touch Interactions**: Swipe gestures and touch-friendly buttons  
- **Camera Access**: Direct camera capture on mobile devices
- **Microphone Access**: Voice recording with permission handling
- **PWA Ready**: Can be installed as a Progressive Web App

## 🔒 Privacy & Security

- **Local Storage**: User preferences stored locally
- **No Data Persistence**: Chat messages not stored permanently
- **Secure Connections**: HTTPS recommended for production
- **Permission Handling**: Proper microphone/camera permission requests

## 🚀 Deployment

### Production Build
```bash
npm run build
npm run start
```

### Docker Deployment
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Environment Setup
- Set `NEXT_PUBLIC_ORCHESTRATOR_URL` to your production backend URL
- Configure proper CORS settings on backend
- Enable HTTPS for production deployment

## 🧪 Testing

### Manual Testing Checklist
- [ ] Text message sending and receiving
- [ ] Voice recording and playback
- [ ] Image upload and preview
- [ ] Backend connection monitoring
- [ ] Responsive design on different screen sizes
- [ ] Error handling and retry mechanisms

### Backend Requirements
Ensure these agents are running before testing:
- Orchestrator Agent (Port 10007)
- Market Agent (Port 10006) 
- Weather Agent (Port 10005)
- Schemes Agent (Port 10004)

## 🛠️ Development

### Project Structure
```
frontend/
├── public/                 # Static assets
├── src/
│   ├── app/               # Next.js app router pages
│   ├── components/        # React components
│   │   ├── ui/           # Reusable UI components
│   │   └── chat/         # Chat-specific components
│   ├── lib/              # Utility functions and API clients
│   ├── types/            # TypeScript type definitions
│   └── styles/           # Global styles
├── package.json          # Dependencies and scripts
├── tailwind.config.js    # Tailwind CSS configuration
└── tsconfig.json        # TypeScript configuration
```

### Key Dependencies
- **Next.js 14**: React framework with app router
- **TypeScript**: Type safety and better DX
- **Tailwind CSS**: Utility-first CSS framework
- **Framer Motion**: Animation library
- **Lucide React**: Modern icon library
- **React Hot Toast**: Toast notifications

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of the Bhumi AI agricultural intelligence initiative.

## 🆘 Support

### Common Issues

**Connection Failed:**
- Verify backend agents are running
- Check `NEXT_PUBLIC_ORCHESTRATOR_URL` configuration
- Ensure CORS is properly configured on backend

**Audio Recording Not Working:**
- Grant microphone permissions
- Use HTTPS in production
- Check browser compatibility

**Image Upload Issues:**
- Verify file size limits (5MB default)
- Check supported formats: PNG, JPG, WebP, GIF
- Ensure proper MIME type handling

### Getting Help
- Check browser console for error messages
- Verify backend agent logs
- Test individual components in isolation
- Review network requests in browser dev tools

---

**🌾 Built for Indian Farmers - Empowering Agriculture Through AI**
