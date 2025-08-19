"""
Custom Request Handler for Agricultural Schemes Intelligence Agent

This module provides a custom A2A request handler that extends the default
request handler with schemes-specific functionality and enhanced error handling.
"""

import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import TaskStore
from a2a.types import (
    GetTaskRequest,
    GetTaskResponse,
)

logger = logging.getLogger(__name__)


class CustomRequestHandler(DefaultRequestHandler):
    """
    Custom A2A request handler for the Agricultural Schemes Intelligence Agent.
    
    This handler extends the default A2A request handler with schemes-specific
    functionality, enhanced logging, and error handling optimized for agricultural
    schemes queries and RAG processing workflows.
    """
    
    def __init__(
        self,
        agent_executor: AgentExecutor,
        task_store: TaskStore,
    ):
        """
        Initialize the custom request handler.
        
        Args:
            agent_executor: The agent executor that handles schemes processing
            task_store: Task store for managing A2A task lifecycle
        """
        super().__init__(agent_executor, task_store)
        logger.info("🔧 Custom request handler initialized for schemes agent")
    
    async def on_message_send(
        self, params, context: RequestContext
    ):
        """
        Handle incoming message send requests with enhanced logging.
        
        Args:
            params: The message parameters
            context: The request context
            
        Returns:
            The result from the parent handler
        """
        try:
            # Extract query for logging
            query = self._extract_query_from_params(params)
            logger.info(f"📨 Processing schemes query: {query[:100]}...")
            
            # Log request metadata
            if hasattr(params, 'message') and params.message:
                session_id = getattr(context, 'session_id', 'unknown')
                logger.info(f"🔗 Session ID: {session_id}")
            
            # Process the request using parent handler
            response = await super().on_message_send(params, context)
            
            # Log successful processing
            logger.info("✅ Schemes query processed successfully")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error processing schemes message: {e}")
            # Re-raise to let parent handler manage error response
            raise
    
    async def on_get_task(self, request: GetTaskRequest) -> GetTaskResponse:
        """
        Handle task status requests with enhanced logging.
        
        Args:
            request: A2A task status request
            
        Returns:
            GetTaskResponse: A2A response with task status
        """
        try:
            # Log task status request
            task_id = getattr(request.params, 'id', 'unknown') if hasattr(request, 'params') else 'unknown'
            logger.debug(f"📋 Task status request for: {task_id}")
            
            # Process the request using parent handler
            response = await super().on_get_task(request)
            
            # Log task status
            if response and hasattr(response, 'result') and response.result:
                task_state = getattr(response.result.status, 'state', 'unknown') if hasattr(response.result, 'status') else 'unknown'
                logger.debug(f"📊 Task {task_id} status: {task_state}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error retrieving task status: {e}")
            # Re-raise to let parent handler manage error response
            raise
    
    def _extract_query_from_params(self, params) -> str:
        """
        Extract the user query from message parameters.
        
        Args:
            params: Message parameters containing the user query
            
        Returns:
            str: The extracted query text or 'unknown query' if not found
        """
        try:
            # Check if params has a message attribute
            if hasattr(params, 'message') and params.message:
                message = params.message
                
                # Check if message has parts
                if hasattr(message, 'parts') and message.parts:
                    for part in message.parts:
                        # Check if part has text content
                        if hasattr(part, 'text') and part.text:
                            return part.text
                        # Check if part has a root with text
                        if hasattr(part, 'root') and hasattr(part.root, 'text'):
                            return part.root.text
                
                # Check if message has direct text attribute
                if hasattr(message, 'text') and message.text:
                    return message.text
            
            # Fallback: check if params itself has text
            if hasattr(params, 'text') and params.text:
                return params.text
                
            return "unknown query"
            
        except Exception as e:
            logger.warning(f"Failed to extract query from params: {e}")
            return "unknown query"
    
    def get_handler_stats(self) -> dict:
        """
        Get statistics about the request handler performance.
        
        Returns:
            dict: Handler statistics and metrics
        """
        try:
            # Basic stats - can be extended with actual metrics tracking
            return {
                "handler_type": "CustomRequestHandler",
                "agent_type": "Agricultural Schemes Intelligence Agent",
                "features": [
                    "Enhanced logging",
                    "Query extraction",
                    "Error handling",
                    "Session tracking"
                ],
                "status": "active"
            }
            
        except Exception as e:
            logger.error(f"Error generating handler stats: {e}")
            return {"error": str(e)}
