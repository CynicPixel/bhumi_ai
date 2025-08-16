#!/usr/bin/env python3
"""Simple script to query the weather agent directly."""

import asyncio
import httpx
from a2a.client import A2AClient
from a2a.types import Message, Part, TextPart, Role, SendMessageRequest, MessageSendParams, AgentCard
import uuid

async def query_weather_agent(query: str):
    """Send a simple query to the weather agent."""
    
    # Set longer timeout for complex weather queries that require multiple API calls
    timeout = httpx.Timeout(120.0)  # 2 minutes timeout
    async with httpx.AsyncClient(timeout=timeout) as httpx_client:
        # Get agent card
        try:
            agent_card_response = await httpx_client.get("http://localhost:10005/.well-known/agent-card.json")
            agent_card_response.raise_for_status()
            agent_card_data = agent_card_response.json()
            print(f"🤖 Connected to: {agent_card_data['name']}")
        except Exception as e:
            print(f"❌ Error fetching agent card: {e}")
            return

        # Create A2A client
        agent_card = AgentCard.model_validate(agent_card_data)
        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)

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

        print(f"📤 Sending: {query}")
        try:
            response = await client.send_message(request)
            print("📥 Response:")
            
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
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    query = input("Enter your weather query: ") or "What's the current weather in Punjab for farming?"
    asyncio.run(query_weather_agent(query))