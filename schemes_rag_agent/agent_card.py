"""
Agent Card Definition for Agricultural Schemes Intelligence Agent

This module defines the A2A Agent Card that describes the capabilities,
skills, and metadata of the Agricultural Schemes Intelligence Agent for
discovery and interaction within the A2A protocol ecosystem.
"""

from a2a.types import AgentCapabilities, AgentCard, AgentSkill


def create_agent_card(host: str = "localhost", port: int = 10004) -> AgentCard:
    """
    Create the Agent Card for the Agricultural Schemes Intelligence Agent.
    
    This agent provides comprehensive information about Indian agricultural schemes,
    government programs, subsidies, and farmer support initiatives using advanced
    RAG (Retrieval-Augmented Generation) capabilities.
    
    Args:
        host: The hostname where the agent is hosted
        port: The port number where the agent is accessible
        
    Returns:
        AgentCard: Complete A2A agent card for discovery and interaction
    """
    
    # Define agent capabilities
    capabilities = AgentCapabilities(
        input_modes=["text"],
        output_modes=["text"],
        streaming=True,
    )
    
    # Define comprehensive agricultural schemes skills
    schemes_skills = [
        AgentSkill(
            id="scheme_discovery_intelligence",
            name="Advanced Agricultural Scheme Discovery & Analysis",
            description="Intelligent discovery and analysis of Indian agricultural schemes with advanced RAG capabilities across 453+ scheme documents and government programs",
            tags=["schemes", "discovery", "analysis", "rag", "government", "agriculture", "india"],
            examples=[
                "What schemes are available for organic farming in India?",
                "Find all subsidies for drip irrigation systems",
                "Show me schemes for dairy farming development",
                "What support is available for cotton farmers in Maharashtra?",
                "List all crop insurance schemes and their coverage"
            ],
        ),
        AgentSkill(
            id="scheme_eligibility_assistance",
            name="Comprehensive Eligibility Analysis & Application Guidance",
            description="Advanced eligibility analysis and step-by-step application guidance for agricultural schemes with personalized recommendations",
            tags=["eligibility", "application", "guidance", "personalized", "analysis", "requirements"],
            examples=[
                "Am I eligible for PM-KISAN scheme as a small farmer?",
                "How can I apply for Pradhan Mantri Fasal Bima Yojana?",
                "What documents do I need for Kisan Credit Card?",
                "Check my eligibility for soil health card scheme",
                "Guide me through PMFBY application process"
            ],
        ),
        AgentSkill(
            id="contextual_scheme_intelligence",
            name="Context-Aware Scheme Intelligence & Conversation Continuity", 
            description="Advanced conversation context awareness with MongoDB persistence for personalized scheme recommendations and continuous dialogue",
            tags=["context", "conversation", "memory", "personalized", "continuity", "mongodb"],
            examples=[
                "Continue our discussion about crop insurance from yesterday",
                "Update me on the scheme we discussed last session",
                "Remember my farming interests and show relevant schemes",
                "What's changed in my recommended schemes since last week?",
                "Follow up on the application process we started"
            ],
        ),
        AgentSkill(
            id="subsidy_benefits_analysis",
            name="Advanced Subsidy & Benefits Analysis",
            description="Comprehensive subsidy calculation, benefits analysis, and financial impact assessment for agricultural programs",
            tags=["subsidies", "benefits", "financial", "analysis", "calculation", "impact"],
            examples=[
                "Calculate potential subsidies for my 5-acre farm",
                "What financial benefits does PM-KISAN provide annually?",
                "Analyze subsidy benefits for solar pump installation",
                "Compare subsidy amounts across different farming schemes",
                "Estimate total benefits from multiple scheme enrollment"
            ],
        ),
        AgentSkill(
            id="specialized_farmer_support",
            name="Specialized Farmer Support & Category-Specific Assistance",
            description="Specialized support for different farmer categories including women farmers, tribal farmers, small/marginal farmers with targeted scheme recommendations",
            tags=["specialized", "women-farmers", "tribal", "small-farmers", "category-specific", "targeted"],
            examples=[
                "What support is available for women farmers in agriculture?",
                "Show schemes specifically for tribal farmers",
                "Programs for small and marginal farmers under 2 acres",
                "Benefits available for young farmers starting agriculture",
                "Special schemes for differently-abled farmers"
            ],
        ),
        AgentSkill(
            id="real_time_scheme_updates",
            name="Real-Time Scheme Updates & Latest Information",
            description="Access to latest scheme updates, new launches, deadline notifications, and policy changes with real-time information retrieval",
            tags=["real-time", "updates", "latest", "deadlines", "notifications", "policy-changes"],
            examples=[
                "What are the latest updates on agricultural schemes?",
                "Any new schemes launched this month?",
                "Current application deadlines for farming schemes",
                "Recent policy changes in crop insurance schemes",
                "Latest amendments to PM-KISAN eligibility criteria"
            ],
        ),
        AgentSkill(
            id="advanced_rag_orchestration", 
            name="Advanced RAG Orchestration & Intelligent Document Retrieval",
            description="Sophisticated RAG orchestration with Pinecone vector search, intelligent document retrieval, and context-aware information synthesis",
            tags=["rag", "orchestration", "pinecone", "vector-search", "synthesis", "advanced"],
            examples=[
                "Find detailed documentation for Pradhan Mantri Kisan Samman Nidhi",
                "Retrieve comprehensive information about crop diversification schemes",
                "Search for schemes related to sustainable agriculture practices",
                "Find all government orders related to farming subsidies",
                "Get technical specifications for agricultural equipment subsidies"
            ],
        ),
    ]
    
    # Create the agent card
    agent_card = AgentCard(
        name="Agricultural Schemes Intelligence Agent",
        description="Advanced AI-powered agricultural schemes assistant with sophisticated RAG capabilities for Indian government programs and farmer support initiatives. Features 453+ scheme documents, intelligent conversation context, personalized recommendations, real-time updates, and comprehensive eligibility analysis using state-of-the-art retrieval-augmented generation technology with Pinecone vector search and MongoDB conversation persistence.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=capabilities,
        skills=schemes_skills,
    )
    
    return agent_card


def get_agent_description() -> str:
    """
    Get a detailed description of the agent's capabilities for logging and documentation.
    
    Returns:
        str: Detailed description of agent capabilities
    """
    return """
    🌾 Agricultural Schemes Intelligence Agent        

    Advanced Capabilities:
    • 453+ Agricultural scheme documents with advanced RAG intelligence
    • Comprehensive knowledge of Indian agricultural schemes and government programs
    • Real-time retrieval of scheme information using sophisticated Pinecone vector search
    • Context-aware responses with MongoDB conversation persistence and session continuity
    • Advanced eligibility analysis and personalized application guidance
    • Specialized support for different farmer categories (women, tribal, small/marginal farmers)
    • Real-time scheme updates, policy changes, and deadline notifications
    • Multi-level subsidy analysis and financial benefit calculations
    • Intelligent conversation context integration across sessions
    • A2A protocol compliance for seamless multi-agent orchestration

    Key Technical Features:
    • Unified RAG with conversation context integration and memory persistence
    • Pinecone-powered similarity search for intelligent document retrieval
    • MongoDB conversation persistence for session continuity and user profiling
    • Advanced eligibility matching and requirement analysis
    • Streaming-capable responses for real-time interaction and user engagement
    • A2A protocol compliance for multi-agent agricultural intelligence ecosystem
    • Sophisticated error handling and graceful failure recovery
    • Context-aware personalized recommendations based on user history

    Specialized Knowledge Areas:
    • PM-KISAN, PMFBY, Kisan Credit Card, and 450+ other schemes
    • Subsidy calculations and financial impact analysis
    • Application processes and document requirements
    • Eligibility criteria analysis and compliance checking
    • Scheme benefits comparison and optimization recommendations
    """
