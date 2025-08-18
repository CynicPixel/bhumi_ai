#!/usr/bin/env python3
"""
Utility script for testing and managing conversations in MongoDB.
This script provides command-line tools to interact with the conversation storage.
"""

import click
import os
from datetime import datetime
from dotenv import load_dotenv
from conversation_helper import get_conversation_helper
from mongo_config import ensure_mongo_connection

load_dotenv()


@click.group()
def cli():
    """Conversation management utility for Bhumi AI Weather Agent."""
    pass


@cli.command()
@click.option('--user-id', required=True, help='User ID to retrieve conversations for')
@click.option('--session-id', help='Specific session ID (optional)')
@click.option('--limit', default=20, help='Maximum number of messages to retrieve')
def get_conversations(user_id: str, session_id: str = None, limit: int = 20):
    """Retrieve conversation history for a user."""
    try:
        ensure_mongo_connection()
        helper = get_conversation_helper()
        
        if session_id:
            conversations = helper.get_conversation_history(user_id, session_id, limit)
            if conversations:
                print(f"\n📱 Conversations for User: {user_id}, Session: {session_id}")
                print("=" * 80)
                for conv in conversations:
                    timestamp = conv['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                    role = conv['role'].upper()
                    if conv['role'] == 'user':
                        print(f"\n👤 [{timestamp}] USER:")
                        print(f"   {conv['message_text']}")
                    else:
                        print(f"\n🤖 [{timestamp}] AI:")
                        print(f"   {conv['response_text']}")
            else:
                print(f"No conversations found for user {user_id}, session {session_id}")
        else:
            # Get all sessions for user
            sessions = helper.get_user_sessions(user_id)
            if sessions:
                print(f"\n📱 User {user_id} has {len(sessions)} sessions:")
                for session in sessions:
                    print(f"   • {session}")
            else:
                print(f"No sessions found for user {user_id}")
                
    except Exception as e:
        print(f"❌ Error: {e}")


@cli.command()
@click.option('--user-id', required=True, help='User ID to get stats for')
def get_stats(user_id: str):
    """Get conversation statistics for a user."""
    try:
        ensure_mongo_connection()
        helper = get_conversation_helper()
        
        stats = helper.get_conversation_stats(user_id)
        
        print(f"\n📊 Conversation Statistics for User: {user_id}")
        print("=" * 50)
        print(f"Total Sessions: {stats['total_sessions']}")
        print(f"Total Messages: {stats['total_messages']}")
        
        if stats['sessions']:
            print(f"\nSession Details:")
            for session in stats['sessions']:
                session_id = session['_id']
                message_count = session['message_count']
                first_msg = session['first_message'].strftime('%Y-%m-%d %H:%M:%S')
                last_msg = session['last_message'].strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"   • {session_id}: {message_count} messages")
                print(f"     First: {first_msg}, Last: {last_msg}")
                
    except Exception as e:
        print(f"❌ Error: {e}")


@cli.command()
@click.option('--user-id', required=True, help='User ID to delete session for')
@click.option('--session-id', required=True, help='Session ID to delete')
def delete_session(user_id: str, session_id: str):
    """Delete a specific session for a user."""
    try:
        ensure_mongo_connection()
        helper = get_conversation_helper()
        
        # Confirm deletion
        click.confirm(f"Are you sure you want to delete session {session_id} for user {user_id}?", abort=True)
        
        success = helper.delete_session(user_id, session_id)
        if success:
            print(f"✅ Successfully deleted session {session_id} for user {user_id}")
        else:
            print(f"❌ Failed to delete session {session_id} for user {user_id}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


@cli.command()
@click.option('--user-id', required=True, help='User ID to test with')
@click.option('--session-id', required=True, help='Session ID to test with')
@click.option('--message', required=True, help='Test message to store')
def test_store(user_id: str, session_id: str, message: str):
    """Test storing a user message and AI response."""
    try:
        ensure_mongo_connection()
        helper = get_conversation_helper()
        
        # Store test user message
        user_msg_id = f"test_msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        success = helper.store_user_message(
            user_id=user_id,
            session_id=session_id,
            message_id=user_msg_id,
            message_text=message,
            context_id="test_context",
            task_id="test_task"
        )
        
        if success:
            print(f"✅ Stored user message: {message}")
        else:
            print(f"❌ Failed to store user message")
            return
        
        # Store test AI response
        ai_msg_id = f"test_resp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        response = f"This is a test AI response to: {message}"
        success = helper.store_ai_response(
            user_id=user_id,
            session_id=session_id,
            message_id=ai_msg_id,
            response_text=response,
            context_id="test_context",
            task_id="test_task"
        )
        
        if success:
            print(f"✅ Stored AI response: {response}")
        else:
            print(f"❌ Failed to store AI response")
            
    except Exception as e:
        print(f"❌ Error: {e}")


@cli.command()
def test_connection():
    """Test MongoDB connection."""
    try:
        ensure_mongo_connection()
        print("✅ MongoDB connection successful!")
        
        # Test collection access
        helper = get_conversation_helper()
        collection = helper.collection
        count = collection.count_documents({})
        print(f"📊 Collection '{collection.name}' has {count} documents")
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")


if __name__ == '__main__':
    cli()
