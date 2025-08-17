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
from dotenv import load_dotenv, find_dotenv
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from mongo_config import ensure_mongo_connection
from logging_config import initialize_logging, log_server_event

# Load environment variables from .env files
# This will search current directory and parent directories for .env files
load_dotenv(find_dotenv(usecwd=True))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""
    pass


def create_agent_card() -> AgentCard:
    """Create the agent card for the Weather Agent."""
    
    # Define skills for weather-related queries
    weather_skills = [
        AgentSkill(
            id="current_weather",
            name="Current Weather Conditions",
            description="Get current weather conditions with agricultural insights for Indian farming",
            tags=["weather", "current", "farming", "agriculture", "india"],
            examples=[
                "What's the current weather in Punjab for farming?",
                "Current weather conditions in Maharashtra",
                "Is it good weather for field work in Karnataka today?"
            ],
        ),
        AgentSkill(
            id="weather_forecast",
            name="Weather Forecast",
            description="Get weather forecasts for agricultural planning (1-16 days)",
            tags=["weather", "forecast", "planning", "farming", "agriculture"],
            examples=[
                "7-day weather forecast for Gujarat",
                "Will it rain in the next 5 days in Tamil Nadu?",
                "Weather forecast for harvesting in Uttar Pradesh"
            ],
        ),
        AgentSkill(
            id="soil_conditions",
            name="Soil Conditions",
            description="Get soil temperature and moisture conditions for planting decisions",
            tags=["soil", "temperature", "moisture", "planting", "agriculture"],
            examples=[
                "Soil conditions for planting in Bihar",
                "Soil temperature and moisture in Rajasthan",
                "Is the soil ready for sowing in Haryana?"
            ],
        ),
        AgentSkill(
            id="spraying_conditions",
            name="Spraying Conditions",
            description="Get optimal conditions for pesticide and herbicide application",
            tags=["spraying", "pesticide", "herbicide", "wind", "conditions"],
            examples=[
                "When should I spray pesticides in West Bengal?",
                "Best time for herbicide application in Madhya Pradesh",
                "Are wind conditions good for spraying in Andhra Pradesh?"
            ],
        ),
        AgentSkill(
            id="historical_weather",
            name="Historical Weather Data",
            description="Get historical weather data for comparison and agricultural planning",
            tags=["historical", "weather", "data", "comparison", "planning"],
            examples=[
                "Historical weather data for last year in Kerala",
                "Compare this year's rainfall with last year in Punjab",
                "Weather patterns in Maharashtra from 2023"
            ],
        ),
    ]

    return AgentCard(
        name="Weather_Agent",
        description="Specialized weather agent providing comprehensive weather information and agricultural guidance for Indian farmers using real-time Open-Meteo API data",
        url="http://localhost:10002/",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        skills=weather_skills,
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=True),
    )


@click.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=10002, help="Port to bind to")
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
