"""
Market Intelligence Agent - Main Entry Point

This module provides the main entry point for running the Market Intelligence Agent
as a standalone application. It demonstrates the agent's capabilities and provides
a testing interface for agricultural market intelligence queries.

Usage:
    python -m market_agent_adk
    
    Or directly:
    python market_agent_adk/__main__.py

Features:
- Interactive testing mode
- Example queries demonstration
- Agent capability showcase
- A2A framework integration testing
"""

import logging
import os

import click
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from custom_request_handler import CustomRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from agent import create_agent
from agent_executor import MarketAgentExecutor
from dotenv import load_dotenv
from mongo_config import ensure_mongo_connection
from logging_config import initialize_logging, log_server_event
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""
    pass


def create_agent_card() -> AgentCard:
    """Create the agent card for the Market Intelligence Agent."""
    
    # Define comprehensive skills for market intelligence queries
    market_skills = [
        AgentSkill(
            id="commodity_price_intelligence",
            name="Comprehensive Commodity Price Intelligence",
            description="Advanced price analysis with city, state, and market-level data across 453+ commodities using CEDA Agmarknet API",
            tags=["prices", "commodity", "market", "agriculture", "india", "analysis", "real-time"],
            examples=[
                "What are the current onion prices in Mumbai?",
                "Get potato prices across all Delhi markets today",
                "Show rice price trends in Punjab over last month",
                "Compare wheat prices between Maharashtra and Haryana",
                "Analyze tomato price movements in Chennai market"
            ],
        ),
        AgentSkill(
            id="market_discovery_intelligence",
            name="Intelligent Market Discovery & Location Resolution",
            description="Advanced market location resolution, market discovery, and geographic intelligence across Indian agricultural markets",
            tags=["markets", "location", "discovery", "geographic", "states", "districts", "cities"],
            examples=[
                "Find all potato markets in Punjab",
                "Where is rice sold in West Bengal?",
                "Show me markets for onions in Maharashtra",
                "What crops are traded in Azadpur market?",
                "Find commodity markets near Chandigarh"
            ],
        ),
        AgentSkill(
            id="supply_chain_analysis",
            name="Advanced Supply Chain & Arrival Analysis",
            description="Comprehensive supply chain analysis with arrival quantities, supply conditions, and market flows across multiple levels",
            tags=["supply", "arrivals", "quantity", "logistics", "analysis", "market-flow"],
            examples=[
                "What are the tomato arrivals in Chennai this week?",
                "Supply analysis for wheat in Haryana markets",
                "Onion arrival patterns in Maharashtra",
                "Cotton supply conditions across Gujarat",
                "Rice arrival trends in Andhra Pradesh"
            ],
        ),
        AgentSkill(
            id="comparative_market_analysis",
            name="Multi-Level Comparative Market Analysis",
            description="Sophisticated comparative analysis across cities, states, markets, and time periods with trend identification",
            tags=["comparison", "analysis", "trends", "multi-level", "benchmark", "insights"],
            examples=[
                "Compare onion prices in Mumbai vs Delhi vs Kolkata",
                "Which state has the best potato prices this month?",
                "Price comparison between Punjab and Haryana wheat markets",
                "Seasonal price trends for cotton across regions",
                "Historical price analysis for rice in eastern states"
            ],
        ),
        AgentSkill(
            id="intelligent_commodity_resolution",
            name="Advanced Commodity Search & Resolution",
            description="Intelligent commodity discovery with multilingual support, fuzzy matching, and access to 453+ commodity database",
            tags=["search", "commodity", "multilingual", "hindi", "bengali", "tamil", "fuzzy-match"],
            examples=[
                "Find prices for 'pyaaz' (Hindi for onion)",
                "Search for 'aloo' rates in Delhi (potato in Hindi)",
                "What commodities are available starting with 'rice'?",
                "Show me all vegetable commodities",
                "Find 'chawal' market data (rice in Hindi)"
            ],
        ),
        AgentSkill(
            id="contextual_market_intelligence",
            name="Contextual Market Intelligence & Conversation Continuity",
            description="Context-aware market analysis with conversation memory, personalized insights, and continued market monitoring",
            tags=["context", "memory", "personalized", "continuity", "insights", "monitoring"],
            examples=[
                "Continue analyzing the onion market from our last conversation",
                "Update me on the commodity we discussed yesterday",
                "What's changed in my focus market since last week?",
                "Provide context-based market recommendations",
                "Remember my trading interests and provide updates"
            ],
        ),
        AgentSkill(
            id="atomic_api_orchestration",
            name="Advanced API Orchestration & Custom Workflows",
            description="Dynamic orchestration of atomic CEDA API tools to create custom market intelligence workflows for complex analysis",
            tags=["orchestration", "workflows", "atomic", "api", "custom", "advanced", "ceda"],
            examples=[
                "Build a custom supply chain analysis for cotton across Gujarat",
                "Create a comprehensive market report for rice in eastern India",
                "Orchestrate multi-state price monitoring for onions",
                "Design a custom trading intelligence workflow",
                "Perform complex market analysis across multiple parameters"
            ],
        ),
    ]

    return AgentCard(
        name="Market Intelligence Agent for Indian Agriculture",
        description="Advanced agricultural market intelligence agent providing comprehensive commodity analysis, real-time pricing, supply chain insights, and trading intelligence for Indian farmers and traders. Features 26+ specialized tools, 453+ commodity database, multi-level analysis (national/state/district/market), and intelligent API orchestration using official CEDA Agmarknet data.",
        url="http://localhost:10006/",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        skills=market_skills,
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=True),
    )


@click.command()
@click.option("--port", default=10006, help="Port to run the server on")
@click.option("--host", default="localhost", help="Host to run the server on")
@click.option("--workers", default=1, help="Number of workers")
def main(port: int, host: str, workers: int):
    """Run the Market Intelligence Agent server."""
    
    # Check for required API key
    if not os.getenv("CEDA_API_KEY"):
        raise MissingAPIKeyError(
            "CEDA_API_KEY environment variable is required. Please set it in your .env file."
        )
    
    # Initialize logging system first
    log_config = initialize_logging()
    logger.info("Starting Market Intelligence Agent server...")
    
    # Initialize MongoDB connection
    try:
        ensure_mongo_connection()
        logger.info("MongoDB connection established successfully")
        log_server_event("MongoDB Connection", "Successfully established MongoDB connection")
    except Exception as e:
        logger.warning(f"Failed to establish MongoDB connection: {e}")
        logger.warning("Continuing without conversation management features")
        log_server_event("MongoDB Connection", f"Failed to establish connection: {e}", error=e)
    
    # Create agent card first
    agent_card = create_agent_card()
    
    # Create agent and executor
    agent = create_agent()
    runner = Runner(
        app_name=agent_card.name,
        agent=agent,
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
        artifact_service=InMemoryArtifactService(),
    )
    
    executor = MarketAgentExecutor(runner)
    task_store = InMemoryTaskStore()
    
    # Create request handler
    request_handler = CustomRequestHandler(
        agent_executor=executor,
        task_store=task_store,
    )
    
    # Create and configure the A2A server
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )
    
    logger.info(f"Market Intelligence Agent server starting on {host}:{port}")
    logger.info("API Documentation available at: http://localhost:10006/docs")
    logger.info("Market Intelligence capabilities:")
    for skill in agent_card.skills:
        logger.info(f"  • {skill.name}: {skill.description}")
    
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
