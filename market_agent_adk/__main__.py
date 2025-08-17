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
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from agent import create_agent
from agent_executor import MarketAgentExecutor
from dotenv import load_dotenv, find_dotenv
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Load environment variables from .env files
# This will search current directory and parent directories for .env files
load_dotenv(find_dotenv(usecwd=True))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""
    pass


def create_agent_card() -> AgentCard:
    """Create the agent card for the Market Intelligence Agent."""
    
    # Define skills for market intelligence queries
    market_skills = [
        AgentSkill(
            id="commodity_prices",
            name="Commodity Price Information",
            description="Get current and historical commodity prices from Indian agricultural markets",
            tags=["prices", "commodity", "market", "agriculture", "india"],
            examples=[
                "What are the current onion prices in Mumbai?",
                "Get potato prices in Delhi today",
                "Show rice prices in Punjab this week"
            ],
        ),
        AgentSkill(
            id="market_comparison",
            name="Market Price Comparison",
            description="Compare commodity prices across multiple markets for better trading decisions",
            tags=["comparison", "market", "prices", "trading", "analysis"],
            examples=[
                "Compare onion prices in Mumbai, Delhi, and Kolkata",
                "Which market has the best potato prices?",
                "Compare wheat prices across Punjab markets"
            ],
        ),
        AgentSkill(
            id="price_trends",
            name="Price Trend Analysis",
            description="Analyze commodity price trends over time for market timing decisions",
            tags=["trends", "analysis", "historical", "timing", "market"],
            examples=[
                "Show onion price trends in Mumbai over last month",
                "Analyze rice price movements in Bihar",
                "Price trend analysis for cotton in Gujarat"
            ],
        ),
        AgentSkill(
            id="supply_analysis",
            name="Market Supply Analysis",
            description="Get commodity arrival and supply data to assess market conditions",
            tags=["supply", "arrivals", "quantity", "market", "conditions"],
            examples=[
                "What are the tomato arrivals in Chennai market?",
                "Market supply conditions for wheat in Haryana",
                "Onion arrival quantities in Maharashtra"
            ],
        ),
        AgentSkill(
            id="multilingual_support",
            name="Multi-language Commodity Recognition",
            description="Support for Hindi, Bengali, Tamil and other Indian language commodity names",
            tags=["hindi", "bengali", "tamil", "multilingual", "india"],
            examples=[
                "pyaaz prices in Mumbai (Hindi for onion)",
                "aloo rates in Delhi (Hindi for potato)",
                "chawal market data in Punjab (Hindi for rice)"
            ],
        ),
    ]

    return AgentCard(
        name="Market_Agent",
        description="Comprehensive agricultural market intelligence agent providing real-time commodity prices, market analysis, and trading insights for Indian farmers and traders using official CEDA Agmarknet data",
        url="http://localhost:10003/",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        skills=market_skills,
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=True),
    )


@click.command()
@click.option("--port", default=10003, help="Port to run the server on")
@click.option("--host", default="localhost", help="Host to run the server on")
@click.option("--workers", default=1, help="Number of workers")
def main(port: int, host: str, workers: int):
    """Run the Market Intelligence Agent server."""
    
    # Check for required API key
    if not os.getenv("CEDA_API_KEY"):
        raise MissingAPIKeyError(
            "CEDA_API_KEY environment variable is required. Please set it in your .env file."
        )
    
    logger.info("Starting Market Intelligence Agent server...")
    
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
    request_handler = DefaultRequestHandler(
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
