import uuid
import httpx
import asyncio
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

AGENT_URL = "http://localhost:10006"  # Port is 10006 as per your __main__.py
PUBLIC_AGENT_CARD_PATH = "/.well-known/agent.json"

async def test_agent(query: str):
    """Sends a query to the running A2A agent server using proper A2A protocol."""
    async with httpx.AsyncClient(timeout=120.0) as httpx_client:
        try:
            # Initialize A2ACardResolver
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=AGENT_URL,
            )

            print(f"📤 Fetching agent card from: {AGENT_URL}{PUBLIC_AGENT_CARD_PATH}...")
            agent_card = await resolver.get_agent_card()
            print("✅ Agent card fetched successfully")

            # Initialize A2A Client
            client = A2AClient(
                httpx_client=httpx_client, 
                agent_card=agent_card
            )
            print("✅ A2AClient initialized")

            # Create the message
            message_payload = Message(
                role=Role.user,
                messageId=str(uuid.uuid4()),
                parts=[Part(root=TextPart(text=query))],
            )
            
            request = SendMessageRequest(
                id=str(uuid.uuid4()),
                params=MessageSendParams(
                    message=message_payload,
                ),
            )
            
            print(f"📤 Sending query: {query}")
            response = await client.send_message(request)
            
            print("\n🤖 Agent Response:")
            print(f"Response type: {type(response)}")
            
            # Let's see what's actually in the response
            print(f"\n📋 Full Response JSON:")
            response_dict = response.model_dump()
            print(response_dict)
            
            # Try to extract the actual response text from the result
            if 'result' in response_dict:
                result = response_dict['result']
                if 'artifacts' in result and result['artifacts']:
                    print(f"\n📝 Found {len(result['artifacts'])} artifacts:")
                    for i, artifact in enumerate(result['artifacts']):
                        print(f"\nArtifact {i+1}:")
                        if 'parts' in artifact:
                            for j, part in enumerate(artifact['parts']):
                                if 'text' in part:
                                    print(f"📄 Part {j+1}: {part['text']}")
                                elif 'root' in part and 'text' in part['root']:
                                    print(f"📄 Part {j+1}: {part['root']['text']}")
                else:
                    print("No artifacts found in result")
            else:
                print("No result field found in response")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    # Ensure the agent server is running in another terminal first
    print("🔍 Market Intelligence Agent Test Client")
    print("Make sure the agent is running on http://localhost:10006")
    print()
    
    test_query = input("Enter your query: ") or "Show me onion prices in Mumbai today"
    asyncio.run(test_agent(test_query))
