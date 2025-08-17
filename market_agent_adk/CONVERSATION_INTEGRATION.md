# Market Agent Conversation Management Integration

## Overview

This document describes the conversation management integration implemented in the Market Agent ADK, similar to the Weather Agent ADK implementation.

## Files Added/Modified

### 1. New Files Added

#### `.env`
- Contains environment variables for MongoDB and other services
- Includes MONGO_URL, DB_NAME, COLLECTION_NAME, and API keys

#### `mongo_config.py`
- MongoDB configuration and connection management
- Handles connection establishment, indexing, and error handling
- Provides global MongoDB instance and helper functions

#### `conversation_helper.py`
- Main conversation management functionality
- Methods for storing user messages and AI responses
- Methods for retrieving conversation history
- Error handling and fallback mechanisms

#### `test_conversation.py`
- Test script to verify conversation management functionality
- Tests MongoDB connection, message storage, and retrieval

### 2. Modified Files

#### `agent_executor.py`
- Added conversation helper import and initialization
- Modified `_run_agent` to accept user_id parameter
- Updated `_process_request` to include conversation management:
  - Extract user messages and store them in MongoDB
  - Retrieve conversation history for context
  - Store AI responses in MongoDB
- Added context parameter handling

#### `agent.py`
- Added conversation helper import
- Added two new conversation management functions:
  - `get_last_conversation()`: Retrieves recent conversation history
  - `get_conversation_context()`: Provides contextual information based on topic/commodity
- Updated agent tools list to include conversation functions
- Enhanced agent instructions with conversation workflow guidance

#### `__main__.py`
- Added MongoDB connection initialization
- Added error handling for MongoDB connection failures
- Ensures conversation management is available when the agent starts

#### `pyproject.toml`
- Added `pymongo` dependency for MongoDB connectivity

## Key Features Implemented

### 1. Conversation Storage
- **User Messages**: Stored with user_id, session_id, message_text, context_id, task_id, and timestamp
- **AI Responses**: Stored with response_text, artifacts, and metadata
- **Unique Message IDs**: Generated using UUID for each conversation turn

### 2. Conversation Retrieval
- **Last Conversations**: Get recent conversation history with configurable limit
- **Conversation Context**: Provide contextual information based on user's focus area
- **Session Management**: Track multiple sessions per user

### 3. Error Handling
- **Graceful Degradation**: Agent continues to work even if MongoDB is unavailable
- **Connection Testing**: Validates MongoDB connection before operations
- **Comprehensive Logging**: Detailed logs for debugging and monitoring

### 4. Agent Integration
- **Context Tools**: Two new tools added to the agent's toolkit
- **Workflow Guidance**: Updated agent instructions to use conversation context
- **Personalized Responses**: Enables more relevant and contextual responses

## Usage in Agent Responses

The agent now has access to two new tools:

1. **`get_conversation_context(topic, commodity)`**
   - Provides context about the user's focus area
   - Helps tailor responses to specific commodities or topics

2. **`get_last_conversation(limit)`**
   - Retrieves recent conversation history
   - Enables continuity across conversation turns

## Workflow Integration

The recommended workflow for the agent is now:

1. Call `get_conversation_context()` to understand user's focus area
2. Call `get_last_conversation()` for conversation continuity
3. Use context to provide more relevant market analysis
4. Reference previous conversations when building on earlier discussions

## Environment Variables Required

```env
GOOGLE_API_KEY=your_google_api_key
MONGO_URL=your_mongodb_connection_string
DB_NAME=Capone
COLLECTION_NAME=Bhumi
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX=agri-rag
```

## Database Schema

### Conversation Documents
```json
{
  "user_id": "string",
  "session_id": "string", 
  "message_id": "string",
  "role": "user|ai",
  "message_text": "string",        // For user messages
  "response_text": "string",       // For AI responses
  "context_id": "string",
  "task_id": "string",
  "artifacts": [{}],               // For AI responses
  "timestamp": "datetime",
  "message_type": "user_input|ai_response"
}
```

### Database Indexes
- `(user_id, session_id)`: For fast conversation retrieval
- `(timestamp, -1)`: For time-based queries
- `(message_id, 1)`: Unique message identification

## Benefits

1. **Contextual Responses**: Agent can reference previous conversations
2. **Personalized Experience**: Tailored responses based on user's focus areas
3. **Conversation Continuity**: Seamless multi-turn conversations
4. **Data Persistence**: All conversations stored for analysis and improvement
5. **Scalable Architecture**: Supports multiple users and sessions

## Testing

Run the test script to verify the integration:

```bash
python test_conversation.py
```

This will test:
- MongoDB connection
- Message storage and retrieval
- Conversation context functions
- Error handling

## Next Steps

1. **Install Dependencies**: Ensure all required packages are installed
2. **Environment Setup**: Configure the .env file with proper credentials
3. **Testing**: Run comprehensive tests to verify functionality
4. **Monitoring**: Set up logging and monitoring for conversation management
5. **Optimization**: Fine-tune conversation retrieval and context generation
