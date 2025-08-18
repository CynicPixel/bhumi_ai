"""
Simple A2A Testing Client for Agricultural Schemes Intelligence Agent

This module provides a simple testing client for the Agricultural Schemes 
Intelligence Agent using the A2A protocol. It demonstrates how to interact
with the agent and can be used for testing and validation.
"""

import asyncio
import uuid
import logging
from typing import Optional

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    Message,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    TextPart,
)

# Configuration
AGENT_URL = "http://localhost:10007"  # Schemes agent port
PUBLIC_AGENT_CARD_PATH = "/.well-known/agent.json"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_schemes_agent(query: str) -> Optional[str]:
    """
    Test the Agricultural Schemes Intelligence Agent using A2A protocol.
    
    Args:
        query: The agricultural schemes query to send to the agent
        
    Returns:
        Optional[str]: The agent's response or None if failed
    """
    async with httpx.AsyncClient(timeout=120.0) as httpx_client:
        try:
            logger.info(f"🌾 Testing Agricultural Schemes Intelligence Agent")
            logger.info(f"🔗 Agent URL: {AGENT_URL}")
            logger.info(f"❓ Query: {query}")
            logger.info("-" * 60)
            
            # Initialize A2A Card Resolver
            logger.info(f"📤 Fetching agent card from: {AGENT_URL}{PUBLIC_AGENT_CARD_PATH}...")
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=AGENT_URL,
            )

            agent_card = await resolver.get_agent_card()
            logger.info("✅ Agent card fetched successfully")
            logger.info(f"📋 Agent: {agent_card.name}")
            logger.info(f"📝 Description: {agent_card.description}")
            logger.info(f"🎯 Version: {agent_card.version}")
            
            if agent_card.skills:
                logger.info("🛠️ Agent Skills:")
                for skill in agent_card.skills:
                    logger.info(f"   • {skill.name}: {skill.description}")

            # Initialize A2A Client
            client = A2AClient(
                httpx_client=httpx_client, 
                agent_card=agent_card,
                url=AGENT_URL
            )
            logger.info("✅ A2A Client initialized")

            # Create the message payload
            message_payload = Message(
                role=Role.user,
                messageId=str(uuid.uuid4()),
                parts=[Part(root=TextPart(text=query))],
            )
            
            # Create the A2A request
            request = SendMessageRequest(
                id=str(uuid.uuid4()),
                params=MessageSendParams(
                    message=message_payload,
                    sessionId=str(uuid.uuid4()),
                    acceptedOutputModes=["text"]
                )
            )

            logger.info("📤 Sending query to schemes agent...")
            
            # Send the message and get response
            send_response = await client.send_message(request)
            
            if send_response and hasattr(send_response, 'result') and send_response.result:
                logger.info("✅ Response received from schemes agent")
                
                # Extract response artifacts
                response_text = ""
                if hasattr(send_response.result, 'artifacts') and send_response.result.artifacts:
                    for artifact in send_response.result.artifacts:
                        if hasattr(artifact, 'parts') and artifact.parts:
                            for part in artifact.parts:
                                if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                    response_text += part.root.text + "\n"
                
                if response_text.strip():
                    logger.info("-" * 60)
                    logger.info("🤖 SCHEMES AGENT RESPONSE:")
                    logger.info("-" * 60)
                    logger.info(response_text.strip())
                    logger.info("-" * 60)
                    return response_text.strip()
                else:
                    logger.warning("⚠️ No text content found in response artifacts")
                    return None
            else:
                logger.error("❌ No valid response received from schemes agent")
                return None

        except httpx.ConnectError:
            logger.error("❌ Connection failed - is the schemes agent running on port 10007?")
            logger.error("💡 Start the agent with: python __main__.py")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error testing schemes agent: {e}")
            return None


async def run_interactive_test():
    """Run an interactive testing session with the schemes agent."""
    print("\n🌾 Agricultural Schemes Intelligence Agent - Interactive Test")
    print("=" * 60)
    print("Enter your questions about agricultural schemes, or 'quit' to exit")
    print("Example queries:")
    print("  • What schemes are available for organic farming?")
    print("  • Tell me about PM-KISAN benefits")
    print("  • How can I apply for crop insurance?")
    print("=" * 60)
    
    while True:
        try:
            query = input("\n❓ Your question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            if not query:
                print("⚠️ Please enter a question.")
                continue
            
            print(f"\n🔍 Processing: {query}")
            response = await test_schemes_agent(query)
            
            if not response:
                print("❌ Failed to get response. Please try again.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


async def run_example_tests():
    """Run a series of example tests to validate the schemes agent."""
    example_queries = [
        "What schemes are available for organic farming in India?",
        "Tell me about PM-KISAN scheme benefits and eligibility",
        "How can I apply for Pradhan Mantri Fasal Bima Yojana?",
        "What subsidies are available for drip irrigation systems?",
        "Explain the Kisan Credit Card scheme"
    ]
    
    print("\n🧪 Running Example Tests")
    print("=" * 60)
    
    success_count = 0
    for i, query in enumerate(example_queries, 1):
        print(f"\n📝 Test {i}/{len(example_queries)}")
        response = await test_schemes_agent(query)
        
        if response:
            success_count += 1
            print(f"✅ Test {i} passed")
        else:
            print(f"❌ Test {i} failed")
    
    print(f"\n📊 Test Results: {success_count}/{len(example_queries)} passed")
    return success_count == len(example_queries)


if __name__ == "__main__":
    print("🌾 Agricultural Schemes Intelligence Agent - A2A Test Client")
    print("Make sure the schemes agent is running on http://localhost:10007")
    
    # Choose test mode
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "interactive":
            asyncio.run(run_interactive_test())
        elif sys.argv[1] == "examples":
            asyncio.run(run_example_tests())
        else:
            # Single query mode
            query = " ".join(sys.argv[1:])
            asyncio.run(test_schemes_agent(query))
    else:
        # Default: single example query
        test_query = "What schemes are available for organic farming in India?"
        print(f"\n🔍 Running default test query: {test_query}")
        asyncio.run(test_schemes_agent(test_query))
