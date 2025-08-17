import uvicorn
import click
import logging
import os
from dotenv import load_dotenv

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
    
    # Define comprehensive agricultural skills
    agricultural_skills = [
        AgentSkill(
            id="market_weather_insights",
            name="Market + Weather Intelligence",
            description="Get combined commodity prices and weather forecasts for optimal farming decisions",
            tags=["market", "weather", "prices", "forecast", "farming", "agriculture", "india"],
            examples=[
                "What are the current onion prices in Mumbai and how will the weather affect farming?",
                "Get potato prices in Delhi today along with weather forecast for farming decisions",
                "Show rice prices in Punjab this week with weather conditions for planting"
            ],
        ),
        AgentSkill(
            id="farming_conditions_analysis",
            name="Comprehensive Farming Conditions",
            description="Analyze current farming conditions using market intelligence and weather data",
            tags=["farming", "conditions", "analysis", "market", "weather", "soil", "agriculture"],
            examples=[
                "Analyze farming conditions for wheat in Haryana",
                "What are the current conditions for tomato farming in Maharashtra?",
                "Assess farming conditions for cotton in Gujarat"
            ],
        ),
        AgentSkill(
            id="seasonal_agricultural_planning",
            name="Seasonal Agricultural Planning",
            description="Get seasonal advice combining market trends and weather patterns for crop planning",
            tags=["seasonal", "planning", "crops", "market", "weather", "agriculture", "india"],
            examples=[
                "Plan my crop rotation for the next 6 months in Bihar",
                "When should I start preparing for monsoon crops in Kerala?",
                "Best crops to plant in Rajasthan this season considering market and weather"
            ],
        ),
        AgentSkill(
            id="regional_farming_comparison",
            name="Regional Farming Comparison",
            description="Compare farming conditions across different Indian states and regions",
            tags=["regional", "comparison", "states", "farming", "market", "weather", "agriculture"],
            examples=[
                "Compare farming conditions for tomatoes across Maharashtra and Karnataka",
                "Which region is better for wheat farming: Punjab or Haryana?",
                "Compare rice farming conditions in West Bengal vs Tamil Nadu"
            ],
        ),
        AgentSkill(
            id="agent_orchestration",
            name="Intelligent Agent Orchestration",
            description="Coordinate multiple specialized agents for comprehensive agricultural intelligence",
            tags=["orchestration", "multi-agent", "coordination", "intelligence", "agriculture"],
            examples=[
                "What agents are available for agricultural queries?",
                "Get capabilities of the Market Intelligence Agent",
                "How does the orchestrator work with specialized agents?"
            ],
        ),
    ]

    return AgentCard(
        name="Agricultural Intelligence Orchestrator",
        description="Intelligent coordinator providing comprehensive agricultural support by orchestrating specialized market and weather agents for Indian farmers. Combines market intelligence, weather forecasts, and soil conditions for holistic farming advice.",
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
    logger.info("✅ A2A application configured")
    
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
        server.build(),
        host=host,
        port=port,
        workers=workers,
        log_level="info",
    )

if __name__ == "__main__":
    main()
