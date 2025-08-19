import uvicorn
import click
import logging
import os
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from agent_executor import AgriculturalOrchestratorExecutor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_agent_card() -> AgentCard:
    """Create the agent card for the Agricultural Intelligence Orchestrator"""
    
    # Define comprehensive agricultural orchestration skills
    agricultural_skills = [
        AgentSkill(
            id="intelligent_agricultural_routing",
            name="Intelligent Agricultural Query Routing & Multi-Agent Coordination",
            description="Primary function: Smart routing of agricultural queries to specialized agents based on dynamic agent card skill matching with multimodal input analysis capabilities",
            tags=["routing", "multimodal", "agent-cards", "skill-matching", "coordination", "delegation", "intelligence"],
            examples=[
                "Get current onion prices in Mumbai with today's weather forecast",
                "Find government schemes for organic farming with eligibility criteria",
                "What are potato prices in Delhi and farming conditions?",
                "Route my fertilizer question to the right agricultural expert",
                "Coordinate market and weather analysis for crop planning decisions"
            ],
        ),
        AgentSkill(
            id="multimodal_query_analysis",
            name="Multimodal Agricultural Query Analysis & Context Understanding",
            description="Advanced analysis of text, images, and multimodal inputs to understand agricultural context before intelligent routing to appropriate specialist agents",
            tags=["multimodal", "image-analysis", "context", "understanding", "agricultural-intelligence", "query-parsing"],
            examples=[
                "Analyze this crop image and route to appropriate specialist",
                "Understand farming equipment photos for expert consultation",
                "Process field condition images for specialist routing",
                "Analyze agricultural documents and route to scheme experts",
                "Parse complex agricultural queries spanning multiple domains"
            ],
        ),
        AgentSkill(
            id="multi_agent_synthesis",
            name="Multi-Agent Response Coordination & Synthesis",
            description="Coordinate responses from multiple specialized agents and synthesize comprehensive agricultural intelligence when queries span multiple domains",
            tags=["coordination", "synthesis", "multi-agent", "integration", "comprehensive", "agricultural-intelligence"],
            examples=[
                "Combine market prices with weather forecasts for planting advice",
                "Synthesize information from weather, market, and scheme agents",
                "Coordinate multiple expert responses for comprehensive guidance",
                "Integrate specialist insights for holistic farming recommendations",
                "Present unified responses from multiple agricultural experts"
            ],
        ),
    ]

    return AgentCard(
        name="Agricultural Intelligence Orchestrator",
        description="Advanced Agricultural Intelligence Router with multimodal analysis capabilities. PRIMARY function: intelligent routing to specialized agents based on dynamic agent card skill matching. Features multi-agent coordination, comprehensive response synthesis, and multimodal input support with personal inference as fallback only.",
        url=f"http://{os.getenv('HOST', 'localhost')}:{os.getenv('PORT', '10007')}/",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        skills=agricultural_skills,
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=True),
        supportsAuthenticatedExtendedCard=False,  # Set to False to avoid the warning
    )

@click.command()
@click.option("--host", default="localhost", help="Host address to bind the server to")
@click.option("--port", default=10007, type=int, help="Port number for the server to listen on")
@click.option("--workers", default=1, help="Number of worker processes")
def main(host: str, port: int, workers: int):
    """Run the Agricultural Intelligence Orchestrator server"""
    
    # Check for required environment variables
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("❌ GOOGLE_API_KEY environment variable is required")
        logger.error("Please set it in your .env file or environment")
        exit(1)
    
    logger.info("🌾 Starting Agricultural Intelligence Orchestrator...")
    logger.info(f"🌐 Server will be running on http://{host}:{port}")
    logger.info("🎯 Orchestrating specialized agents for comprehensive agricultural support")
    
    # Create agent card
    agent_card = create_agent_card()
    logger.info("✅ Agent card created successfully")
    
    # Create request handler with orchestrator executor
    request_handler = DefaultRequestHandler(
        agent_executor=AgriculturalOrchestratorExecutor(),
        task_store=InMemoryTaskStore(),
    )
    logger.info("✅ Request handler configured")
    
    # Create A2A Starlette application
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )
    
    # Build the app and add CORS middleware
    app = server.build()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    logger.info("✅ A2A application configured with CORS support")
    
    # Log available capabilities
    logger.info("🔧 Available Agricultural Capabilities:")
    for skill in agent_card.skills:
        logger.info(f"  • {skill.name}: {skill.description}")
    
    # Add warning if no agents are configured
    market_url = os.getenv("MARKET_AGENT_URL", "http://localhost:10006")
    weather_url = os.getenv("WEATHER_AGENT_URL", "http://localhost:10005")
    logger.info(f"📍 Market Agent URL: {market_url}")
    logger.info(f"📍 Weather Agent URL: {weather_url}")
    logger.info("⚠️  Note: Ensure these agents are running before testing orchestration")
    logger.info("🚀 The orchestrator will automatically discover and connect to available agents")
    
    logger.info(f"🚀 Starting server on {host}:{port}...")
    
    # Start the server
    uvicorn.run(
        app,
        host=host,
        port=port,
        workers=workers,
        log_level="info",
    )

if __name__ == "__main__":
    main()
