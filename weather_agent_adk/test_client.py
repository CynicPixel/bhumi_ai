import asyncio
import uuid
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


BASE_URL = "http://localhost:10005"
PUBLIC_AGENT_CARD_PATH = "/.well-known/agent-card.json"


async def test_weather_agent():
    """Test the Weather Agent with various farming-related queries."""
    
    print("🌾 Testing Weather Agent for Indian Farmers")
    print("=" * 50)
    
    async with httpx.AsyncClient() as httpx_client:
        # Initialize A2A Card Resolver
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=BASE_URL,
        )

        try:
            print(f"📡 Fetching agent card from: {BASE_URL}{PUBLIC_AGENT_CARD_PATH}")
            agent_card = await resolver.get_agent_card()
            print("✅ Successfully fetched agent card")
            print(f"🤖 Agent: {agent_card.name}")
            print(f"📝 Description: {agent_card.description}")
            
            # Display available skills
            print(f"\n🛠️ Available Skills ({len(agent_card.skills)}):")
            for skill in agent_card.skills:
                print(f"   • {skill.name}: {skill.description}")
            
        except Exception as e:
            print(f"❌ Error fetching agent card: {e}")
            return

        # Initialize A2A Client
        client = A2AClient(
            httpx_client=httpx_client, 
            agent_card=agent_card
        )
        print("\n🔗 A2A Client initialized")

        # Test queries for Indian farmers
        test_queries = [
            "What's the current weather in Punjab for farming?",
            "7-day weather forecast for Maharashtra",
            "Soil conditions for planting in Karnataka",
            "When should I spray pesticides in Gujarat? Check next 24 hours",
            "Historical weather data for last month in Tamil Nadu",
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Test {i}: {query}")
            print("-" * 40)
            
            try:
                # Create message
                message = Message(
                    role=Role.user,
                    messageId=str(uuid.uuid4()),
                    parts=[Part(root=TextPart(text=query))],
                )
                
                # Create request
                request = SendMessageRequest(
                    id=str(uuid.uuid4()),
                    params=MessageSendParams(message=message),
                )
                
                print("📤 Sending request...")
                response = await client.send_message(request)
                
                print("📥 Response received:")
                
                # Extract and display the response
                if hasattr(response, 'root') and hasattr(response.root, 'result'):
                    result = response.root.result
                    if hasattr(result, 'artifacts') and result.artifacts:
                        for artifact in result.artifacts:
                            if hasattr(artifact, 'parts') and artifact.parts:
                                for part in artifact.parts:
                                    if hasattr(part, 'text'):
                                        print(part.text)
                    else:
                        print("No artifacts found in response")
                else:
                    print("Unexpected response format")
                    print(response.model_dump_json(indent=2))
                
            except Exception as e:
                print(f"❌ Error with query '{query}': {e}")
            
            # Wait between requests
            await asyncio.sleep(2)

        print(f"\n✅ Weather Agent testing completed!")


if __name__ == "__main__":
    print("🚀 Starting Weather Agent Test Client")
    print("⚠️  Make sure the Weather Agent is running on http://localhost:10005")
    print("💡 Start the agent with: uv run . from the weather_agent_adk directory")
    print()
    
    try:
        asyncio.run(test_weather_agent())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
