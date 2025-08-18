import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    Message,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
    Task,
    TextPart,
)
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class RemoteAgentManager:
    """Manages connections and communication with remote A2A agents"""
    
    def __init__(self):
        self.agent_connections: Dict[str, A2AClient] = {}
        self.agent_cards: Dict[str, AgentCard] = {}
        self.httpx_client: Optional[httpx.AsyncClient] = None
        
    async def discover_agents(self, agent_configs: Dict[str, str]) -> bool:
        """Discover and connect to available agents"""
        if self.httpx_client is None:
            self.httpx_client = httpx.AsyncClient(timeout=30.0)
        
        success_count = 0
        for agent_name, agent_url in agent_configs.items():
            try:
                logger.info(f"🔍 Discovering agent: {agent_name} at {agent_url}")
                
                # Resolve agent card
                resolver = A2ACardResolver(
                    httpx_client=self.httpx_client,
                    base_url=agent_url,
                )
                
                agent_card = await resolver.get_agent_card()
                logger.info(f"✅ Discovered {agent_name}: {agent_card.name}")
                
                # Create A2A client
                client = A2AClient(
                    httpx_client=self.httpx_client,
                    agent_card=agent_card,
                    url=agent_url
                )
                
                # Store connections
                self.agent_connections[agent_name] = client
                self.agent_cards[agent_name] = agent_card
                success_count += 1
                
                logger.info(f"✅ Connected to {agent_name}")
                
            except Exception as e:
                logger.error(f"❌ Failed to connect to {agent_name} at {agent_url}: {e}")
                continue
        
        logger.info(f"🎯 Successfully connected to {success_count}/{len(agent_configs)} agents")
        return success_count > 0
    
    async def send_to_agent(self, agent_name: str, message: str) -> str:
        """Send message to specific agent and get response"""
        if agent_name not in self.agent_connections:
            raise ValueError(f"Agent {agent_name} not found")
        
        client = self.agent_connections[agent_name]
        
        # Create message request using proper A2A types
        message_id = str(uuid.uuid4())
        
        # Create Message object (this is what MessageSendParams expects)
        message_payload = Message(
            role=Role.user,
            messageId=message_id,
            parts=[Part(root=TextPart(text=message))],
        )
        
        # Create MessageSendParams with the Message object
        message_request = SendMessageRequest(
            id=message_id, 
            params=MessageSendParams(message=message_payload)
        )
        
        try:
            logger.info(f"📤 Sending message to {agent_name}: {message[:100]}...")
            send_response: SendMessageResponse = await client.send_message(message_request)
            
            if not isinstance(send_response.root, SendMessageSuccessResponse):
                logger.error(f"❌ {agent_name} returned non-success response")
                return f"Error: {agent_name} could not process the request"
            
            if not isinstance(send_response.root.result, Task):
                logger.error(f"❌ {agent_name} did not return a task")
                return f"Error: {agent_name} response format invalid"
            
            # Extract response content
            response_content = send_response.root.model_dump_json(exclude_none=True)
            json_content = json.loads(response_content)
            
            response_text = ""
            if json_content.get("result", {}).get("artifacts"):
                for artifact in json_content["result"]["artifacts"]:
                    if artifact.get("parts"):
                        for part in artifact["parts"]:
                            if part.get("text"):
                                response_text += part["text"] + " "
            
            response_text = response_text.strip()
            if not response_text:
                response_text = f"Received response from {agent_name} but no text content found"
            
            logger.info(f"✅ Received response from {agent_name}: {response_text[:100]}...")
            return response_text
            
        except Exception as e:
            logger.error(f"❌ Error communicating with {agent_name}: {e}")
            return f"Error communicating with {agent_name}: {str(e)}"
    
    async def broadcast_query(self, message: str) -> Dict[str, str]:
        """Send the same query to all available agents and collect responses"""
        if not self.agent_connections:
            return {"error": "No agents available"}
        
        responses = {}
        tasks = []
        
        for agent_name in self.agent_connections.keys():
            task = asyncio.create_task(self.send_to_agent(agent_name, message))
            tasks.append((agent_name, task))
        
        # Wait for all responses
        for agent_name, task in tasks:
            try:
                response = await task
                responses[agent_name] = response
            except Exception as e:
                responses[agent_name] = f"Error: {str(e)}"
        
        return responses
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent names"""
        return list(self.agent_connections.keys())
    
    def get_agent_card(self, agent_name: str) -> Optional["AgentCard"]:
        """Get the full agent card for a specific agent"""
        return self.agent_cards.get(agent_name)
    
    def get_agent_info(self, agent_name: str) -> Optional[Dict]:
        """Get information about a specific agent"""
        if agent_name not in self.agent_cards:
            return None
            
        card = self.agent_cards[agent_name]
        return {
            "name": card.name,
            "description": card.description,
            "url": f"http://localhost:{self._get_port_from_agent_name(agent_name)}",
            "skills": [skill.name for skill in card.skills] if card.skills else []
        }
    
    def _get_port_from_agent_name(self, agent_name: str) -> str:
        """Extract port from agent name for URL construction"""
        if "Market" in agent_name:
            return "10006"
        elif "Weather" in agent_name:
            return "10005"
        elif "Schemes" in agent_name or "Agricultural Schemes" in agent_name:
            return "10004"
        else:
            return "10000"  # Default fallback
    
    async def close(self):
        """Close all connections"""
        if self.httpx_client:
            await self.httpx_client.aclose()
            self.httpx_client = None
        logger.info("🔌 Closed all agent connections")
