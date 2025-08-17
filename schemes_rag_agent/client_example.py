#!/usr/bin/env python3
"""
Client example for the Schemes RAG Agent API.
This script demonstrates how to interact with the API endpoints.
"""

import requests
import json
import uuid
from typing import Dict, Any

class SchemesRAGClient:
    """Client for interacting with the Schemes RAG Agent API."""
    
    def __init__(self, base_url: str = "http://localhost:8010"):
        """Initialize the client with the base URL."""
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health status of the API."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Health check failed: {str(e)}"}
    
    def start_conversation(self, user_id: str, session_id: str = None) -> Dict[str, Any]:
        """Start a new conversation session."""
        try:
            params = {"user_id": user_id}
            if session_id:
                params["session_id"] = session_id
                
            response = self.session.post(f"{self.base_url}/conversation/start", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to start conversation: {str(e)}"}
    
    def process_query(
        self, 
        query: str, 
        user_id: str, 
        session_id: str,
        context_id: str = None,
        task_id: str = None
    ) -> Dict[str, Any]:
        """Process a query and get an AI response."""
        try:
            payload = {
                "query": query,
                "user_id": user_id,
                "session_id": session_id
            }
            
            if context_id:
                payload["context_id"] = context_id
            if task_id:
                payload["task_id"] = task_id
            
            response = self.session.post(f"{self.base_url}/query", json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to process query: {str(e)}"}
    
    def get_conversation_history(
        self, 
        user_id: str, 
        session_id: str, 
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get conversation history for a user and session."""
        try:
            params = {
                "user_id": user_id,
                "session_id": session_id,
                "limit": limit
            }
            
            response = self.session.get(f"{self.base_url}/conversation/history", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to get conversation history: {str(e)}"}
    
    def get_config(self) -> Dict[str, Any]:
        """Get current API configuration."""
        try:
            response = self.session.get(f"{self.base_url}/config")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to get config: {str(e)}"}

def demo_conversation():
    """Demonstrate a complete conversation flow."""
    print("🚀 Schemes RAG Agent API Demo")
    print("=" * 50)
    
    # Initialize client
    client = SchemesRAGClient()
    
    # Check health
    print("🔍 Checking API health...")
    health = client.health_check()
    if "error" in health:
        print(f"❌ Health check failed: {health['error']}")
        print("Make sure the server is running on http://localhost:8000")
        return
    
    print(f"✅ API is healthy: {health['status']}")
    print(f"   Components: {health['components']}")
    
    # Get configuration
    print("\n⚙️  Getting API configuration...")
    config = client.get_config()
    if "error" not in config:
        print(f"✅ Model: {config['model']}")
        print(f"   Max tokens: {config['max_tokens']}")
        print(f"   Temperature: {config['temperature']}")
    
    # Start conversation
    user_id = f"demo_user_{uuid.uuid4().hex[:8]}"
    session_id = f"demo_session_{uuid.uuid4().hex[:8]}"
    
    print(f"\n💬 Starting conversation for user: {user_id}")
    conv_start = client.start_conversation(user_id, session_id)
    if "error" in conv_start:
        print(f"❌ Failed to start conversation: {conv_start['error']}")
        return
    
    print(f"✅ Conversation started: {conv_start['session_id']}")
    
    # Sample agricultural scheme queries
    sample_queries = [
        "What are the benefits of PM Kisan scheme?",
        "How can I apply for PM Fasal Bima Yojana?",
        "What is the eligibility criteria for Kisan Credit Card?",
        "Tell me about the Soil Health Card scheme"
    ]
    
    print(f"\n🤖 Processing {len(sample_queries)} sample queries...")
    
    for i, query in enumerate(sample_queries, 1):
        print(f"\n--- Query {i} ---")
        print(f"👤 User: {query}")
        
        # Process query
        response = client.process_query(query, user_id, session_id)
        if "error" in response:
            print(f"❌ Error: {response['error']}")
            continue
        
        print(f"🤖 AI: {response['response'][:200]}...")
        print(f"   RAG Context Used: {response['rag_context_used']}")
        print(f"   Message ID: {response['message_id']}")
    
    # Get conversation history
    print(f"\n📚 Getting conversation history...")
    history = client.get_conversation_history(user_id, session_id, limit=5)
    if "error" not in history:
        print(f"✅ Retrieved {history['count']} messages")
        for conv in history['conversations']:
            role = "👤 User" if conv['role'] == 'user' else "🤖 AI"
            content = conv.get('message_text') or conv.get('response_text', '')[:100]
            print(f"   {role}: {content}...")
    else:
        print(f"❌ Failed to get history: {history['error']}")
    
    print(f"\n🎉 Demo completed successfully!")
    print(f"   User ID: {user_id}")
    print(f"   Session ID: {session_id}")

def interactive_mode():
    """Interactive mode for testing the API."""
    print("🎮 Interactive Mode - Schemes RAG Agent API")
    print("=" * 50)
    
    client = SchemesRAGClient()
    
    # Check if server is running
    health = client.health_check()
    if "error" in health:
        print("❌ Server is not accessible. Please start the server first.")
        return
    
    print("✅ Server is running and healthy!")
    
    # Get user info
    user_id = input("Enter user ID (or press Enter for auto-generated): ").strip()
    if not user_id:
        user_id = f"interactive_user_{uuid.uuid4().hex[:8]}"
    
    session_id = input("Enter session ID (or press Enter for auto-generated): ").strip()
    if not session_id:
        session_id = f"interactive_session_{uuid.uuid4().hex[:8]}"
    
    print(f"👤 User ID: {user_id}")
    print(f"💬 Session ID: {session_id}")
    
    # Start conversation
    conv_start = client.start_conversation(user_id, session_id)
    if "error" in conv_start:
        print(f"❌ Failed to start conversation: {conv_start['error']}")
        return
    
    print("✅ Conversation started!")
    print("\n💡 Type your questions about agricultural schemes (type 'quit' to exit)")
    print("   Type 'history' to see conversation history")
    print("   Type 'config' to see API configuration")
    
    while True:
        try:
            query = input("\n👤 You: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            elif query.lower() == 'history':
                history = client.get_conversation_history(user_id, session_id, limit=10)
                if "error" not in history:
                    print(f"\n📚 Conversation History ({history['count']} messages):")
                    for conv in history['conversations']:
                        role = "👤 User" if conv['role'] == 'user' else "🤖 AI"
                        content = conv.get('message_text') or conv.get('response_text', '')
                        print(f"   {role}: {content}")
                else:
                    print(f"❌ Failed to get history: {history['error']}")
                continue
            elif query.lower() == 'config':
                config = client.get_config()
                if "error" not in config:
                    print(f"\n⚙️  API Configuration:")
                    for key, value in config.items():
                        print(f"   {key}: {value}")
                else:
                    print(f"❌ Failed to get config: {config['error']}")
                continue
            elif not query:
                continue
            
            # Process query
            print("🤖 Processing...")
            response = client.process_query(query, user_id, session_id)
            
            if "error" in response:
                print(f"❌ Error: {response['error']}")
            else:
                print(f"🤖 AI: {response['response']}")
                print(f"   (RAG Context: {'Used' if response['rag_context_used'] else 'Not used'})")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

def main():
    """Main function with menu options."""
    print("🚀 Schemes RAG Agent API Client")
    print("=" * 40)
    print("1. Run demo conversation")
    print("2. Interactive mode")
    print("3. Exit")
    
    while True:
        try:
            choice = input("\nSelect option (1-3): ").strip()
            
            if choice == '1':
                demo_conversation()
                break
            elif choice == '2':
                interactive_mode()
                break
            elif choice == '3':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1, 2, or 3.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
