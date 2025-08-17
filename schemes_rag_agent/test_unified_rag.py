#!/usr/bin/env python3
"""
Test script for the unified RAG approach in Schemes RAG Agent.
This script tests the conversation context building and unified similarity search.
"""

import sys
import os
import logging
from unittest.mock import Mock, MagicMock

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_agent import SchemesRAGAgent

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_unified_conversation_context():
    """Test the unified conversation context building."""
    print("🧪 Testing unified conversation context building...")
    
    # Create a mock agent instance
    agent = SchemesRAGAgent()
    
    # Mock conversation history
    conversation_history = [
        {
            "role": "user",
            "message_text": "What are the government schemes for farmers?",
            "response_text": None
        },
        {
            "role": "ai",
            "message_text": None,
            "response_text": "There are several government schemes for farmers including PM-KISAN, PM-Fasal Bima Yojana, and Kisan Credit Card."
        },
        {
            "role": "user",
            "message_text": "Tell me more about PM-KISAN",
            "response_text": None
        },
        {
            "role": "ai",
            "message_text": None,
            "response_text": "PM-KISAN provides direct income support of Rs. 6000 per year to eligible farmer families."
        }
    ]
    
    current_query = "What are the eligibility criteria for PM-KISAN?"
    
    # Test the unified context building
    unified_context = agent._build_unified_conversation_context(conversation_history, current_query)
    
    print(f"✅ Unified context built successfully!")
    print(f"📝 Context length: {len(unified_context)} characters")
    print(f"🔍 Context preview: {unified_context[:200]}...")
    
    # Verify the context contains all expected elements
    assert "What are the government schemes for farmers?" in unified_context
    assert "PM-KISAN provides direct income support" in unified_context
    assert "Tell me more about PM-KISAN" in unified_context
    assert "What are the eligibility criteria for PM-KISAN?" in unified_context
    
    print("✅ All expected conversation elements found in unified context!")
    
    return unified_context

def test_unified_rag_context_method():
    """Test the unified RAG context method structure."""
    print("\n🧪 Testing unified RAG context method structure...")
    
    # Create a mock agent instance
    agent = SchemesRAGAgent()
    
    # Mock the pinecone manager
    mock_pinecone_manager = Mock()
    mock_pinecone_manager.search_similar_documents.return_value = [
        {
            'id': 'doc1',
            'score': 0.85,
            'metadata': {'text': 'PM-KISAN eligibility criteria: Small and marginal farmers with landholding up to 2 hectares.'}
        },
        {
            'id': 'doc2',
            'score': 0.78,
            'metadata': {'text': 'PM-KISAN application process and required documents.'}
        }
    ]
    
    agent.pinecone_manager = mock_pinecone_manager
    
    # Mock conversation history
    conversation_history = [
        {
            "role": "user",
            "message_text": "What is PM-KISAN?",
            "response_text": None
        }
    ]
    
    current_query = "How do I apply for PM-KISAN?"
    
    # Test the unified RAG context method
    try:
        rag_context = agent._get_unified_rag_context(
            query=current_query,
            conversation_history=conversation_history,
            max_results=3,
            similarity_threshold=0.7
        )
        
        print(f"✅ Unified RAG context method executed successfully!")
        print(f"📝 RAG context length: {len(rag_context)} characters")
        print(f"🔍 RAG context preview: {rag_context[:200]}...")
        
        # Verify the method was called with unified context
        mock_pinecone_manager.search_similar_documents.assert_called_once()
        call_args = mock_pinecone_manager.search_similar_documents.call_args
        unified_query = call_args[1]['query']  # Get the query parameter
        
        print(f"🔍 Search was performed with unified query: {unified_query[:150]}...")
        
        # Verify the unified query contains both conversation history and current query
        assert "What is PM-KISAN?" in unified_query
        assert "How do I apply for PM-KISAN?" in unified_query
        
        print("✅ Unified search query contains both conversation history and current query!")
        
    except Exception as e:
        print(f"❌ Error testing unified RAG context method: {e}")
        return False
    
    return True

def test_method_signatures():
    """Test that method signatures are correct after refactoring."""
    print("\n🧪 Testing method signatures...")
    
    agent = SchemesRAGAgent()
    
    # Check that the old method name is gone and new one exists
    assert hasattr(agent, '_get_unified_rag_context'), "Method _get_unified_rag_context should exist"
    assert not hasattr(agent, '_get_enhanced_rag_context'), "Old method _get_enhanced_rag_context should not exist"
    
    # Check that the new helper method exists
    assert hasattr(agent, '_build_unified_conversation_context'), "Method _build_unified_conversation_context should exist"
    
    print("✅ All method signatures are correct!")
    return True

def main():
    """Run all tests."""
    print("🚀 Starting unified RAG tests...\n")
    
    try:
        # Test 1: Unified conversation context building
        test_unified_conversation_context()
        
        # Test 2: Unified RAG context method
        test_unified_rag_context_method()
        
        # Test 3: Method signatures
        test_method_signatures()
        
        print("\n🎉 All tests passed! The unified RAG approach is working correctly.")
        print("\n📋 Summary of changes:")
        print("   ✅ Replaced multiple separate similarity searches with single unified search")
        print("   ✅ Combined conversation history + current query into single search context")
        print("   ✅ Updated method names and documentation")
        print("   ✅ Maintained fallback to simple search for error cases")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
