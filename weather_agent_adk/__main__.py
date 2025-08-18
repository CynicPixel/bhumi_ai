import logging
import os

import click
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from custom_request_handler import CustomRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from agent import create_agent
from agent_executor import WeatherAgentExecutor
from dotenv import load_dotenv
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from mongo_config import ensure_mongo_connection
from logging_config import initialize_logging, log_server_event

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""
    pass


def create_agent_card() -> AgentCard:
    """Create the agent card for the Weather Agent."""
    
    # Define skills that match the actual comprehensive agent capabilities
    weather_skills = [
        AgentSkill(
            id="comprehensive_farm_conditions",
            name="Comprehensive Farm Conditions Analysis",
            description="Get complete agricultural dashboard including current weather, soil conditions, forecasts, and farming recommendations for any location",
            tags=["weather", "soil", "farming", "agriculture", "comprehensive", "dashboard"],
            examples=[
                "Weather and soil conditions for Chandigarh",
                "Complete farm conditions analysis for Punjab",
                "Agricultural dashboard for Maharashtra farming",
                "Current conditions for farming in Gujarat"
            ],
        ),
        AgentSkill(
            id="spraying_analysis",
            name="Advanced Spraying Analysis & Timing",
            description="Professional analysis of optimal conditions for pesticide, herbicide, and fertilizer application with detailed timing recommendations",
            tags=["spraying", "pesticide", "herbicide", "fertilizer", "timing", "wind", "conditions"],
            examples=[
                "When should I spray pesticides in West Bengal?",
                "Best spraying conditions for next 3 days in Punjab",
                "Professional spraying analysis for Maharashtra",
                "Optimal pesticide application timing in Gujarat",
                "Fertilizer application timing for Durgapur, West Bengal"
            ],
        ),
        AgentSkill(
            id="planting_window_analysis",
            name="Optimal Planting Window Analysis",
            description="Analyze soil and weather conditions to determine the best planting dates for specific crops",
            tags=["planting", "timing", "soil", "weather", "crops", "agriculture"],
            examples=[
                "Best time to plant wheat in Punjab?",
                "Optimal planting window for rice in West Bengal",
                "When should I sow cotton in Gujarat?",
                "Planting schedule for vegetables in Karnataka"
            ],
        ),
        AgentSkill(
            id="irrigation_scheduling",
            name="Precision Irrigation Scheduling",
            description="Generate detailed irrigation schedules based on weather forecasts, soil moisture, and crop water requirements",
            tags=["irrigation", "water", "scheduling", "moisture", "agriculture"],
            examples=[
                "Irrigation schedule for next week in Haryana",
                "Water management plan for Punjab wheat fields",
                "Drip irrigation timing for Maharashtra vineyards",
                "Weekly irrigation schedule for Tamil Nadu rice"
            ],
        ),
        AgentSkill(
            id="disease_risk_analysis",
            name="Crop Disease Risk Assessment",
            description="Analyze weather conditions to assess disease risk and provide prevention recommendations for crops",
            tags=["disease", "risk", "crops", "prevention", "agriculture", "health"],
            examples=[
                "Disease risk for tomato crop in Maharashtra",
                "Fungal disease risk for rice in West Bengal",
                "Crop health analysis for Punjab wheat",
                "Disease prevention for Karnataka vegetables"
            ],
        ),
        AgentSkill(
            id="weather_forecast",
            name="Agricultural Weather Forecasts",
            description="Get detailed weather forecasts with agricultural insights for farming planning (1-16 days)",
            tags=["weather", "forecast", "planning", "farming", "agriculture"],
            examples=[
                "7-day agricultural forecast for Gujarat",
                "Weather forecast for harvesting in Uttar Pradesh",
                "Farming weather outlook for next 2 weeks in Bihar"
            ],
        ),
        AgentSkill(
            id="historical_weather",
            name="Historical Weather Analysis",
            description="Get historical weather data for comparison, trend analysis, and agricultural planning",
            tags=["historical", "weather", "data", "comparison", "planning", "trends"],
            examples=[
                "Historical weather comparison for Punjab",
                "Rainfall trends analysis for Maharashtra",
                "Weather patterns for crop planning in Gujarat"
            ],
        ),
    ]

    return AgentCard(
        name="Weather Agent for Indian Farmers",
        description="Advanced agricultural weather intelligence agent providing comprehensive farm condition analysis, irrigation scheduling, spraying optimization, planting recommendations, and disease risk assessment for Indian farmers using real-time Open-Meteo API data with location-aware precision",
        url="http://localhost:10005/",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        skills=weather_skills,
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=True),
    )


@click.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=10005, help="Port to bind to")
def main(host: str, port: int):
    """Run the Weather Agent server for Indian farmers."""
    try:
        # Check for API key only if Vertex AI is not configured
        if not os.getenv("GOOGLE_GENAI_USE_VERTEXAI") == "TRUE":
            if not os.getenv("GOOGLE_API_KEY"):
                raise MissingAPIKeyError(
                    "GOOGLE_API_KEY environment variable not set and GOOGLE_GENAI_USE_VERTEXAI is not TRUE."
                )
        
        print("🌾 Starting Weather Agent for Indian Farmers...")
        print(f"🌐 Server will be running on http://{host}:{port}")
        print("📍 Covering all major Indian agricultural regions")
        print("🌤️ Real-time weather data from Open-Meteo API")
        
        # Initialize logging system
        try:
            logging_config = initialize_logging(log_level=logging.INFO, log_dir="logs")
            print(f"✅ Logging system initialized")
            print(f"📁 Log files: {logging_config['log_path']}")
            print(f"🆔 Session ID: {logging_config['session_id']}")
        except Exception as e:
            print(f"⚠️  Warning: Logging system failed to initialize: {e}")
            print("   Logging will be disabled")
        
        # Initialize MongoDB connection
        try:
            ensure_mongo_connection()
            print("✅ MongoDB connection established for conversation storage")
        except Exception as e:
            print(f"⚠️  Warning: MongoDB connection failed: {e}")
            print("   Conversation storage will be disabled")
        
        # Create agent card
        agent_card = create_agent_card()
        
        # Create ADK agent
        adk_agent = create_agent()
        
        # Create runner
        runner = Runner(
            app_name=agent_card.name,
            agent=adk_agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )
        
        # Create agent executor
        weather_agent_executor = WeatherAgentExecutor(runner)
        
        # Create request handler
        request_handler = CustomRequestHandler(
            agent_executor=weather_agent_executor,
            task_store=InMemoryTaskStore(),
        )
        
        # Create and configure the A2A server
        server = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler,
        )
        
        print("✅ Weather Agent initialized successfully!")
        print("\n🔧 Available capabilities:")
        for skill in agent_card.skills:
            print(f"   • {skill.name}: {skill.description}")
        
        print(f"\n🚀 Starting server on port {port}...")
        
        # Log server startup
        try:
            log_server_event(
                event_type="startup",
                details=f"Server starting on {host}:{port}",
                host=host,
                port=port,
                session_id=logging_config.get('session_id', 'unknown')
            )
        except Exception as e:
            print(f"⚠️  Warning: Could not log server startup event: {e}")
        
        # Run the server
        uvicorn.run(server.build(), host=host, port=port)
        
    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        logger.error("Please set your GOOGLE_API_KEY in the .env file")
        logger.error("Get your API key from: https://ai.google.dev/")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)


if __name__ == "__main__":
    main()
