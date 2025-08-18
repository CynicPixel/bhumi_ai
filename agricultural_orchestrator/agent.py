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
        **Role:** You are an Advanced Agricultural Intelligence Router with multimodal analysis capabilities. Your PRIMARY function is intelligent routing to specialized agents based on their agent card skills. Personal inference is a FALLBACK option only.

        **ABSOLUTE RULE: NEVER SUMMARIZE AGENT RESPONSES - ALWAYS PRESENT THEM COMPLETELY AND VERBATIM**

        **CORE OPERATIONAL FRAMEWORK:**

        **PRIMARY FUNCTION - INTELLIGENT ROUTING:**
        1. **Multimodal Query Analysis**: Analyze text, images, and other inputs to understand the complete query context
        2. **Agent Card Skill Matching**: Query available agents and match user requests to agent skills and capabilities  
        3. **Multi-Agent Coordination**: Route to multiple agents when queries span multiple domains
        4. **Comprehensive Response Synthesis**: Present complete agent responses with minimal modification

        **ROUTING DECISION PROCESS:**
        1. **Parse Query**: Understand user intent, context, and requirements (including images if provided)
        2. **Query Agent Cards**: Use `list_available_agents` and `get_agent_capabilities` to get current agent skills
        3. **Skill Matching**: Match query requirements to specific agent skills and capabilities
        4. **Route Intelligently**: Use `send_message_to_agent` to delegate to appropriate specialists
        5. **Multi-Agent Coordination**: For complex queries, route to multiple agents as needed

        **Available Specialized Agents:**
        {self.agent_info}

        **ROUTING PRIORITY (Always try these first):**
        * **Weather/Soil/Climate/Fertilizer/Irrigation queries** → Weather Agent for Indian Farmers
        * **Commodity/Price/Market/Trading queries** → Market Intelligence Agent for Indian Agriculture  
        * **Government Schemes/Subsidies/Application queries** → Agricultural Schemes Intelligence Agent
        * **Multi-domain queries** → Route to ALL relevant agents and synthesize responses

        **FALLBACK - Personal Inference (ONLY when):**
        * No agents are available for the query type
        * Agent cards indicate no relevant skills match
        * General agricultural knowledge requests that don't require specialized data
        * Follow-up questions that need clarification before routing

        **RESPONSE STRATEGY:**
        * **Primary**: Always attempt routing first - present agent responses COMPLETELY AND VERBATIM
        * **Quote Full Responses**: When agents provide detailed information, present their EXACT response text without summarizing
        * **Multi-Agent**: For complex queries, coordinate multiple agents and present ALL their complete responses
        * **Verbatim Presentation**: Do NOT summarize, paraphrase, or shorten agent responses - present them in full
        * **Fallback**: Provide direct analysis only when routing is not possible or appropriate
        * **Transparency**: Always indicate which agents were consulted, then present their complete responses

        **CRITICAL INSTRUCTION FOR AGENT RESPONSES:**
        When you receive a response from an agent via `send_message_to_agent`, you MUST present the complete response text exactly as received. Do NOT summarize, paraphrase, or provide overview - present the full detailed content the agent provided. Users want the complete specialized information, not a summary.
        
        **EXAMPLE OF CORRECT BEHAVIOR:**
        User asks: "Tell me about government loan schemes"
        You call: send_message_to_agent("Agricultural Schemes Intelligence Agent", "Tell me about government loan schemes")
        Agent returns: "किसान क्रेडिट कार्ड (Kisan Credit Card - KCC): This scheme provides farmers with timely and adequate credit..."
        You respond: "I consulted the Agricultural Schemes Intelligence Agent. Here's their detailed response:
        
        किसान क्रेडिट कार्ड (Kisan Credit Card - KCC): This scheme provides farmers with timely and adequate credit..."
        
        **WRONG BEHAVIOR - DO NOT DO THIS:**
        ❌ "I consulted the agent and they provided information about various schemes"
        ❌ "The agent mentioned several loan programs including..."
        ❌ Any form of summarizing or paraphrasing agent responses

        **MULTIMODAL CAPABILITIES:**
        * Analyze images of crops, fields, equipment, documents for better routing decisions
        * Use visual context to enhance query understanding before routing
        * Include image analysis in agent requests when relevant

        **Tools for Smart Delegation:**
        - `list_available_agents`: See all agents with their detailed skills and capabilities
        - `get_agent_capabilities`: Get detailed information about a specific agent's skills  
        - `send_message_to_agent`: Delegate query to the most appropriate agent based on skills analysis

        **Today's Date (YYYY-MM-DD):** {datetime.now().strftime("%Y-%m-%d")}

        **Remember:** You are primarily a SMART ROUTER that leverages specialized agent expertise. Use your own knowledge as backup only when routing is not feasible.
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
            logger.info(f"✅ Received response from {agent_name}: {response[:200]}...")
            logger.info(f"🔍 FULL RESPONSE LENGTH: {len(response)} characters")
            logger.info(f"🔍 FULL RESPONSE CONTENT: {response}")
            return response
        except Exception as e:
            logger.error(f"❌ Error sending message to {agent_name}: {e}")
            return f"Error communicating with {agent_name}: {str(e)}"

    async def list_available_agents(self, tool_context: ToolContext) -> str:
        """List available specialized agents with their detailed capabilities from agent cards"""
        if not self.available_agents:
            return "❌ No specialized agents are currently available. Please check agent connections."
        
        agent_details = "🎯 **Available Specialized Agents with Skills:**\n\n"
        
        for agent_name in self.available_agents:
            agent_card = self.remote_manager.get_agent_card(agent_name)
            if agent_card:
                agent_details += f"**{agent_card.name}**\n"
                agent_details += f"� {agent_card.description}\n"
                agent_details += f"🌐 URL: {agent_card.url}\n"
                
                if hasattr(agent_card, 'skills') and agent_card.skills:
                    agent_details += f"�️ **Skills ({len(agent_card.skills)}):**\n"
                    for skill in agent_card.skills:
                        agent_details += f"  • **{skill.name}**: {skill.description}\n"
                        if hasattr(skill, 'tags') and skill.tags:
                            agent_details += f"    Tags: {', '.join(skill.tags[:5])}\n"  # Show first 5 tags
                        if hasattr(skill, 'examples') and skill.examples:
                            example = skill.examples[0] if skill.examples else "No examples"
                            agent_details += f"    Example: \"{example}\"\n"
                else:
                    agent_details += "🛠️ Skills: Not specified\n"
                
                agent_details += "\n"
            else:
                # Fallback for agents without cards
                info = self.remote_manager.get_agent_info(agent_name)
                if info:
                    agent_details += f"**{info['name']}**\n"
                    agent_details += f"📝 {info['description']}\n"
                    agent_details += f"🌐 URL: {info['url']}\n"
                    if info['skills']:
                        agent_details += f"�️ Skills: {', '.join(info['skills'])}\n"
                    agent_details += "\n"
        
        agent_details += "💡 **Usage:** Use `send_message_to_agent` with the exact agent name to delegate specialized queries based on their skills."
        
        return agent_details
    
    async def get_agent_capabilities(self, agent_name: str, tool_context: ToolContext) -> str:
        """Get detailed capabilities of a specific agent using their agent card"""
        if not agent_name:
            return "❌ Please specify an agent name to get capabilities."
        
        agent_card = self.remote_manager.get_agent_card(agent_name)
        if not agent_card:
            return f"❌ Agent '{agent_name}' not found or not available."
        
        capabilities = f"🔍 **Detailed Agent Capabilities: {agent_card.name}**\n\n"
        capabilities += f"📝 **Description:** {agent_card.description}\n"
        capabilities += f"🌐 **URL:** {agent_card.url}\n"
        capabilities += f"📊 **Version:** {agent_card.version}\n"
        
        if hasattr(agent_card, 'capabilities') and agent_card.capabilities:
            capabilities += f"⚙️ **Technical Capabilities:**\n"
            caps = agent_card.capabilities
            if hasattr(caps, 'input_modes') and caps.input_modes:
                capabilities += f"  • Input Modes: {', '.join(caps.input_modes)}\n"
            if hasattr(caps, 'output_modes') and caps.output_modes:
                capabilities += f"  • Output Modes: {', '.join(caps.output_modes)}\n"
            if hasattr(caps, 'streaming'):
                capabilities += f"  • Streaming: {'Yes' if caps.streaming else 'No'}\n"
        
        if hasattr(agent_card, 'skills') and agent_card.skills:
            capabilities += f"\n🛠️ **Skills ({len(agent_card.skills)} total):**\n"
            for i, skill in enumerate(agent_card.skills, 1):
                capabilities += f"\n**{i}. {skill.name}**\n"
                capabilities += f"   📋 Description: {skill.description}\n"
                
                if hasattr(skill, 'tags') and skill.tags:
                    capabilities += f"   🏷️ Tags: {', '.join(skill.tags)}\n"
                
                if hasattr(skill, 'examples') and skill.examples:
                    capabilities += f"   💡 Examples:\n"
                    for example in skill.examples[:3]:  # Show first 3 examples
                        capabilities += f"      • \"{example}\"\n"
        else:
            capabilities += "\n🛠️ **Skills:** Not specified in agent card\n"
        
        capabilities += f"\n💡 **Usage:** Send queries to this agent using `send_message_to_agent(\"{agent_card.name}\", \"your query\")`"
        
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
