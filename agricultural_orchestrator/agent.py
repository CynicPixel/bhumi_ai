import asyncio
import logging
import os
from typing import Any, AsyncIterable, Dict, List, Optional
from datetime import datetime

import nest_asyncio
from google.adk import Agent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from dotenv import load_dotenv

from remote_agent_manager import RemoteAgentManager
from agricultural_tools import AgriculturalTools

load_dotenv()
nest_asyncio.apply()

logger = logging.getLogger(__name__)

class AgriculturalOrchestrator:
    """Intelligent orchestrator agent for agricultural support in India"""
    
    def __init__(self):
        self.remote_manager = RemoteAgentManager()
        self.available_agents: List[str] = []
        self.agent_info: str = ""
        self._agent: Optional[Agent] = None
        self._runner: Optional[Runner] = None
        self._user_id = "agricultural_orchestrator"
        
    @classmethod
    async def create(cls):
        """Create and initialize the orchestrator following A2A best practices"""
        instance = cls()
        await instance._async_init_components()
        return instance
    
    async def _async_init_components(self):
        """Initialize components and discover agents BEFORE creating the ADK agent"""
        logger.info("🚀 Initializing Agricultural Orchestrator components...")
        
        # Agent configuration - update these URLs to match your running agents
        agent_configs = {
            "Market Intelligence Agent for Indian Agriculture": os.getenv("MARKET_AGENT_URL", "http://localhost:10006"),
            "Weather Agent for Indian Farmers": os.getenv("WEATHER_AGENT_URL", "http://localhost:10005"),
            "Agricultural Schemes Intelligence Agent": os.getenv("SCHEMES_AGENT_URL", "http://localhost:10004")
        }
        
        # Discover and connect to available agents FIRST
        success = await self.remote_manager.discover_agents(agent_configs)
        if success:
            self.available_agents = self.remote_manager.get_available_agents()
            logger.info(f"✅ Discovered {len(self.available_agents)} agents: {self.available_agents}")
            
            # Build agent info string for instruction
            agent_info_list = []
            for agent_name in self.available_agents:
                info = self.remote_manager.get_agent_info(agent_name)
                if info:
                    agent_info_list.append(f"• **{info['name']}**: {info['description']}")
                else:
                    agent_info_list.append(f"• **{agent_name}**: Available for queries")
            
            self.agent_info = "\n".join(agent_info_list) if agent_info_list else "No specialized agents currently available"
        else:
            logger.warning("⚠️ No agents could be discovered")
            self.available_agents = []
            self.agent_info = "No specialized agents currently available"
        
        # Create ADK agent AFTER discovering agents
        self._agent = self.create_agent()
        
        # Create runner AFTER agent creation
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )
        
        # Initialize agricultural tools AFTER everything else
        self.agricultural_tools = AgriculturalTools(self.remote_manager)
        
        logger.info("✅ Agricultural Orchestrator components initialized successfully")
    
    def create_agent(self) -> Agent:
        """Create the ADK agent with agricultural orchestration capabilities"""
        return Agent(
            model=os.getenv("GOOGLE_MODEL_NAME", "gemini-2.0-flash-exp"),
            name="Agricultural_Intelligence_Orchestrator",
            instruction=self.root_instruction,
            description="Intelligent coordinator providing comprehensive agricultural support by orchestrating specialized market, weather, and schemes agents for Indian farmers",
            tools=[
                self.send_message_to_agent,
                self.list_available_agents,
                self.get_agent_capabilities
            ],
        )
    
    def root_instruction(self, context: ReadonlyContext) -> str:
        """Root instruction for the agricultural orchestrator"""
        return f"""
        **Role:** You are an expert Agricultural Intelligence Routing Delegator. Your primary function is to accurately delegate user inquiries regarding agriculture to the appropriate specialized remote agents.

        **Core Directives:**

        * **Task Delegation:** Utilize the `send_message_to_agent` function to assign actionable tasks to remote agents.
        * **Intelligent Routing:** Analyze user queries and automatically route them to the most appropriate agent based on their capabilities.
        * **Contextual Awareness for Remote Agents:** If a remote agent needs context, enrich the task description with all necessary contextual information relevant to that specific agent.
        * **Autonomous Agent Engagement:** Never seek user permission before engaging with remote agents. Route queries directly to the appropriate specialized agents.
        * **Transparent Communication:** Always present the complete and detailed response from the remote agent to the user.
        * **No Redundant Confirmations:** Do not ask remote agents for confirmation of information or actions.
        * **Tool Reliance:** Strictly rely on the send_message_to_agent tool to address user requests. Do not generate responses based on assumptions.
        * **Comprehensive Context:** When routing to agents, include the full user query and any relevant context.

        **Available Specialized Agents:**
        {self.agent_info}

        **Routing Guidelines:**
        * **Weather/Soil/Climate queries** → Route to "Weather Agent for Indian Farmers"  
        * **Commodity/Price/Market queries** → Route to "Market Intelligence Agent for Indian Agriculture"
        * **Government Schemes/Subsidies queries** → Route to "Agricultural Schemes Intelligence Agent"
        * **Mixed queries** → Route to the most relevant primary agent or multiple agents if needed

        **Today's Date (YYYY-MM-DD):** {datetime.now().strftime("%Y-%m-%d")}

        **Remember:** You are a routing coordinator that MUST delegate all agricultural queries to specialized agents using send_message_to_agent. Never provide direct answers - always route to the appropriate expert agent.
        """
    
    async def send_message_to_agent(
        self,
        agent_name: str,
        message: str,
        tool_context: ToolContext
    ) -> str:
        """Send a message to a specific specialized agent.
        
        Use this tool to delegate any agricultural query to the appropriate specialized agent.
        Analyze the user's query and route it to the best agent based on their capabilities:
        
        - Weather Agent for Indian Farmers: Weather, soil, climate, spraying conditions, irrigation timing
        - Market Intelligence Agent for Indian Agriculture: Commodity prices, market trends, trading insights  
        - Agricultural Schemes Intelligence Agent: Government schemes, subsidies, eligibility, applications
        
        Args:
            agent_name: The exact name of the agent to send the message to
            message: The complete user query with full context
        """
        if agent_name not in self.available_agents:
            return f"❌ Agent '{agent_name}' is not available. Available agents: {', '.join(self.available_agents)}"
        
        try:
            logger.info(f"🎯 Routing message to {agent_name}: {message[:100]}...")
            response = await self.remote_manager.send_to_agent(agent_name, message)
            logger.info(f"✅ Received response from {agent_name}: {response[:100]}...")
            return response
        except Exception as e:
            logger.error(f"❌ Error sending message to {agent_name}: {e}")
            return f"Error communicating with {agent_name}: {str(e)}"

    async def list_available_agents(self, tool_context: ToolContext) -> str:
        """List available specialized agents and their capabilities"""
        if not self.available_agents:
            return "❌ No specialized agents are currently available. Please check agent connections."
        
        agent_list = "🎯 **Available Specialized Agents:**\n\n"
        
        for agent_name in self.available_agents:
            info = self.remote_manager.get_agent_info(agent_name)
            if info:
                agent_list += f"**{info['name']}**\n"
                agent_list += f"📍 URL: {info['url']}\n"
                agent_list += f"📝 Description: {info['description']}\n"
                if info['skills']:
                    agent_list += f"🛠️ Skills: {', '.join(info['skills'])}\n"
                agent_list += "\n"
            else:
                agent_list += f"**{agent_name}**\n"
                agent_list += f"📝 Status: Available for queries\n\n"
        
        return agent_list
    
    async def get_agent_capabilities(self, agent_name: str, tool_context: ToolContext) -> str:
        """Get detailed capabilities of a specific agent"""
        if not agent_name:
            return "❌ Please specify an agent name to get capabilities."
        
        info = self.remote_manager.get_agent_info(agent_name)
        if not info:
            return f"❌ Agent '{agent_name}' not found or not available."
        
        capabilities = f"🔍 **Agent Capabilities: {info['name']}**\n\n"
        capabilities += f"📝 **Description:** {info['description']}\n"
        capabilities += f"🌐 **URL:** {info['url']}\n"
        
        if info['skills']:
            capabilities += f"🛠️ **Skills:**\n"
            for skill in info['skills']:
                capabilities += f"  • {skill}\n"
        else:
            capabilities += f"🛠️ **Skills:** No specific skills listed\n"
        
        return capabilities
    
    async def invoke(self, query: str, session_id: str) -> AsyncIterable[dict]:
        """Main orchestration workflow - processes user queries"""
        logger.info(f"🎯 Processing query for session {session_id}: {query[:100]}...")
        
        # Get or create session
        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )
        
        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                session_id=session_id,
                state={},
            )
            logger.info(f"✅ Created new session {session_id}")
        
        # Create user content
        user_content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=query)]
        )
        
        # Process with ADK runner
        async for event in self._runner.run_async(
            user_id=self._user_id,
            session_id=session.id,
            new_message=user_content
        ):
            if event.is_final_response():
                response_text = ""
                if event.content and event.content.parts and event.content.parts[-1].text:
                    response_text = event.content.parts[-1].text
                
                logger.info(f"✅ Final response for session {session_id}")
                yield {
                    'is_task_complete': True,
                    'content': response_text,
                }
            else:
                yield {
                    'is_task_complete': False,
                    'updates': "🌾 Analyzing your agricultural query and coordinating with specialized agents...",
                }
    
    async def close(self):
        """Clean up resources"""
        await self.remote_manager.close()
        logger.info("🔌 Agricultural Orchestrator resources cleaned up")
