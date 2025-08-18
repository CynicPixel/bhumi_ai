"""
Agent Executor for Agricultural Schemes Intelligence Agent

This module provides the core A2A agent executor that bridges the A2A protocol
with the existing schemes RAG capabilities, enabling seamless integration with
the multi-agent agricultural intelligence ecosystem.
"""

import logging
import uuid
from typing import Optional, Dict, Any

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, TextPart, UnsupportedOperationError
from a2a.utils.errors import ServerError

from conversation_helper import get_conversation_helper
from rag_agent import SchemesRAGAgent

logger = logging.getLogger(__name__)


class SchemesAgentExecutor(AgentExecutor):
    """
    Agent executor that bridges A2A protocol with Schemes RAG capabilities.
    
    This executor handles the translation between A2A requests and the existing
    schemes RAG processing pipeline, ensuring seamless integration while preserving
    all existing RAG functionality and conversation context.
    """
    
    def __init__(self):
        """Initialize the schemes agent executor."""
        self.rag_agent: Optional[SchemesRAGAgent] = None
        self.conversation_helper = None
        self._initialized = False
        logger.info("🚀 Initializing Schemes Agent Executor...")
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """Initialize RAG agent and conversation helper components."""
        try:
            # Initialize existing RAG agent
            logger.info("📚 Initializing RAG agent...")
            self.rag_agent = SchemesRAGAgent()
            
            if not self.rag_agent.initialize():
                raise RuntimeError("Failed to initialize schemes RAG agent")
            
            logger.info("✅ RAG agent initialized successfully")
            
            # Initialize A2A conversation helper
            logger.info("💬 Initializing conversation helper...")
            try:
                self.conversation_helper = get_conversation_helper()
                logger.info("✅ Conversation helper initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize conversation helper: {e}")
                self.conversation_helper = None
            
            self._initialized = True
            logger.info("🎯 Schemes Agent Executor fully initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize schemes agent executor: {e}")
            raise RuntimeError(f"Schemes agent executor initialization failed: {e}")
    
    def _is_initialized(self) -> bool:
        """Check if the executor is properly initialized."""
        return (
            self._initialized and 
            self.rag_agent is not None and 
            self.rag_agent._is_initialized()
        )
    
    def _extract_user_id(self, context: RequestContext) -> str:
        """
        Extract user ID from A2A request context.
        
        Args:
            context: A2A request context
            
        Returns:
            str: User identifier for conversation tracking
        """
        try:
            # Try to extract user ID from call context
            if context.call_context and hasattr(context.call_context, 'user'):
                if hasattr(context.call_context.user, 'user_name'):
                    return context.call_context.user.user_name
                elif hasattr(context.call_context.user, 'id'):
                    return context.call_context.user.id
            
            # Fallback to session ID or generate one
            if context.session_id:
                return f"user_{context.session_id}"
            
            # Last resort - generate a unique user ID
            return f"schemes_user_{uuid.uuid4().hex[:8]}"
            
        except Exception as e:
            logger.warning(f"Failed to extract user ID: {e}")
            return f"anonymous_user_{uuid.uuid4().hex[:8]}"
    
    def _generate_message_id(self) -> str:
        """Generate a unique message ID."""
        return str(uuid.uuid4())
    
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """
        Execute schemes query processing using A2A protocol.
        
        This is the main execution method that:
        1. Extracts user query from A2A context
        2. Manages conversation context
        3. Processes query through RAG pipeline
        4. Streams results back via A2A events
        
        Args:
            context: A2A request context containing user message
            event_queue: A2A event queue for streaming updates
        """
        if not self._is_initialized():
            logger.error("❌ Schemes agent executor not initialized")
            raise ServerError("Schemes agent not properly initialized")
        
        # Extract request information
        if not context.message:
            raise ValueError('Message should be present in request context')
        
        query = context.get_user_input()
        user_id = self._extract_user_id(context)
        session_id = context.context_id or str(uuid.uuid4())
        context_id = context.context_id or str(uuid.uuid4())
        task_id = context.task_id or str(uuid.uuid4())
        
        logger.info(f"🔍 Processing schemes query for user: {user_id}, session: {session_id}")
        logger.info(f"📝 Query: {query[:100]}...")
        
        # Store user message in conversation context
        if self.conversation_helper:
            try:
                message_id = self._generate_message_id()
                # stored = self.conversation_helper.store_user_message(
                #     user_id=user_id,
                #     session_id=session_id,
                #     message_text=query,
                #     context_id=context_id,
                #     task_id=task_id,
                #     message_id=message_id
                # )
                if stored:
                    logger.info(f"💾 User message stored with ID: {message_id}")
                else:
                    logger.warning("⚠️ Failed to store user message")
            except Exception as e:
                logger.warning(f"Failed to store user message: {e}")
        
        # Create task updater for A2A status updates
        task_updater = TaskUpdater(event_queue, task_id, context_id)
        
        try:
            # Submit and start task processing
            await task_updater.submit()
            await task_updater.start_work()
            
            # Update status to indicate RAG processing
            await task_updater.update_status(
                TaskState.working,
                message=task_updater.new_agent_message([
                    TextPart(text="🔍 Searching agricultural schemes database...")
                ])
            )
            
            # Process query through existing RAG pipeline
            logger.info("🧠 Processing query through RAG pipeline...")
            result = self.rag_agent.process_query(
                query=query,
                user_id=user_id,
                session_id=session_id,
                context_id=context_id,
                task_id=task_id
            )
            
            if result["success"]:
                response_text = result["response"]
                logger.info(f"✅ RAG processing successful, response length: {len(response_text)}")
                
                # Store AI response in conversation context
                if self.conversation_helper:
                    try:
                        ai_message_id = self._generate_message_id()
                        # stored = self.conversation_helper.store_ai_response(
                        #     user_id=user_id,
                        #     session_id=session_id,
                        #     response_text=response_text,
                        #     context_id=context_id,
                        #     task_id=task_id,
                        #     message_id=ai_message_id,
                        #     metadata=result
                        # )
                        # if stored:
                        #     logger.info(f"💾 AI response stored with ID: {ai_message_id}")
                    except Exception as e:
                        logger.warning(f"Failed to store AI response: {e}")
                
                # Convert RAG response to A2A artifacts
                text_parts = [TextPart(text=response_text)]
                
                # Complete A2A task with artifacts (same pattern as ADK agents)
                await task_updater.add_artifact(text_parts)
                await task_updater.complete()
                
                logger.info("🎯 Schemes query completed successfully")
                
            else:
                # Handle RAG processing errors
                error_message = result.get("response", "Failed to process agricultural schemes query")
                logger.error(f"❌ RAG processing failed: {result.get('error', 'Unknown error')}")
                
                await task_updater.update_status(
                    TaskState.failed,
                    message=task_updater.new_agent_message([
                        TextPart(text=error_message)
                    ])
                )
        
        except Exception as e:
            logger.error(f"❌ Error in schemes agent execution: {e}")
            
            # Send error status update
            try:
                await task_updater.update_status(
                    TaskState.failed,
                    message=task_updater.new_agent_message([
                        TextPart(text="I encountered an error while processing your agricultural schemes query. Please try again.")
                    ])
                )
            except Exception as update_error:
                logger.error(f"Failed to send error status update: {update_error}")
            
            # Re-raise the original exception
            raise ServerError(f"Schemes processing error: {str(e)}")
    
    async def cancel(
        self, 
        context: RequestContext, 
        event_queue: EventQueue
    ) -> None:
        """
        Handle task cancellation requests.
        
        Args:
            context: A2A request context
            event_queue: A2A event queue
        """
        logger.info(f"⚠️ Task cancellation requested for context: {context.context_id}")
        
        # For now, schemes processing doesn't support cancellation
        # This could be enhanced to interrupt long-running RAG operations
        raise ServerError(error=UnsupportedOperationError())
    
    def get_executor_status(self) -> Dict[str, Any]:
        """
        Get the current status of the schemes agent executor.
        
        Returns:
            Dict[str, Any]: Executor status and statistics
        """
        try:
            return {
                "executor_type": "SchemesAgentExecutor",
                "initialized": self._initialized,
                "rag_agent_ready": self.rag_agent is not None and self.rag_agent._is_initialized(),
                "conversation_helper_ready": self.conversation_helper is not None and self.conversation_helper.is_initialized(),
                "capabilities": [
                    "Agricultural schemes RAG processing",
                    "Conversation context management", 
                    "A2A protocol integration",
                    "Streaming response support",
                    "MongoDB conversation persistence",
                    "Pinecone vector search"
                ],
                "status": "ready" if self._is_initialized() else "not_ready"
            }
        except Exception as e:
            logger.error(f"Error generating executor status: {e}")
            return {
                "executor_type": "SchemesAgentExecutor",
                "error": str(e),
                "status": "error"
            }
    
    def close(self) -> None:
        """Close the executor and cleanup resources."""
        try:
            if self.rag_agent:
                self.rag_agent.close()
                logger.info("🔌 RAG agent closed")
            
            if self.conversation_helper:
                self.conversation_helper.close()
                logger.info("🔌 Conversation helper closed")
            
            self._initialized = False
            logger.info("🔌 Schemes agent executor closed")
            
        except Exception as e:
            logger.error(f"Error closing schemes agent executor: {e}")
