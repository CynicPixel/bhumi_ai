#!/usr/bin/env python3
"""
Test script for conversation management in Market Agent ADK.

This script tests the conversation helper functionality and MongoDB integration.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from conversation_helper import get_conversation_helper
from mongo_config import ensure_mongo_connection

# Load environment variables
load_dotenv()

async def test_conversation_management():
    """Test the conversation management functionality."""
    print("🧪 Testing Market Agent Conversation Management")
    print("=" * 50)
    
    # Test 1: MongoDB Connection
    print("\n1. Testing MongoDB Connection...")
    try:
        ensure_mongo_connection()
        print("✅ MongoDB connection successful")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return
    
    # Test 2: Conversation Helper Initialization
    print("\n2. Testing Conversation Helper...")
    try:
        helper = get_conversation_helper()
        print("✅ Conversation helper initialized")
    except Exception as e:
        print(f"❌ Conversation helper initialization failed: {e}")
        return
    
    # Test 3: Store User Message
    print("\n3. Testing User Message Storage...")
    try:
        test_user_id = "test_market_user"
        test_session_id = "test_market_session"
        test_message_id = f"test_msg_{int(datetime.now().timestamp())}"
        test_message = "What are the current wheat prices in Punjab?"
        
        success = helper.store_user_message(
            user_id=test_user_id,
            session_id=test_session_id,
            message_id=test_message_id,
            message_text=test_message,
            context_id="test_context",
            task_id="test_task"
        )
        
        if success:
            print(f"✅ User message stored: {test_message_id}")
        else:
            print(f"❌ Failed to store user message: {test_message_id}")
    except Exception as e:
        print(f"❌ User message storage failed: {e}")
    
    # Test 4: Store AI Response
    print("\n4. Testing AI Response Storage...")
    try:
        test_response_id = f"test_resp_{int(datetime.now().timestamp())}"
        test_response = "Based on the latest market data, wheat prices in Punjab are showing an upward trend..."
        
        success = helper.store_ai_response(
            user_id=test_user_id,
            session_id=test_session_id,
            message_id=test_response_id,
            response_text=test_response,
            context_id="test_context",
            task_id="test_task",
            artifacts=[]
        )
        
        if success:
            print(f"✅ AI response stored: {test_response_id}")
        else:
            print(f"❌ Failed to store AI response: {test_response_id}")
    except Exception as e:
        print(f"❌ AI response storage failed: {e}")
    
    # Test 5: Retrieve Conversation History
    print("\n5. Testing Conversation History Retrieval...")
    try:
        conversations = helper.get_last_conversations(
            user_id=test_user_id,
            session_id=test_session_id,
            limit=5
        )
        
        print(f"✅ Retrieved {len(conversations)} conversations")
        for i, conv in enumerate(conversations, 1):
            role = conv.get('role', 'unknown')
            text = conv.get('message_text', conv.get('response_text', 'No text'))[:50]
            timestamp = conv.get('timestamp', 'No timestamp')
            print(f"   {i}. [{role.upper()}] {text}... ({timestamp})")
            
    except Exception as e:
        print(f"❌ Conversation history retrieval failed: {e}")
    
    # Test 6: Test Conversation Context Functions
    print("\n6. Testing Conversation Context Functions...")
    try:
        # Import the agent functions
        from agent import get_conversation_context, get_last_conversation
        
        # Test conversation context
        context_result = await get_conversation_context(topic="price trends", commodity="wheat")
        print("✅ Conversation context function works")
        print(f"   Context length: {len(context_result)} characters")
        
        # Test last conversation
        last_conv_result = await get_last_conversation(limit=3)
        print("✅ Last conversation function works")
        print(f"   Result length: {len(last_conv_result)} characters")
        
    except Exception as e:
        print(f"❌ Conversation context functions failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Conversation Management Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_conversation_management())
