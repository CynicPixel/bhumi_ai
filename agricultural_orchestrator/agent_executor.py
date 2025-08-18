import logging
import uuid
from collections.abc import AsyncIterable

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    Task,
    TaskState,
    UnsupportedOperationError,
)
from a2a.utils import (
    new_agent_text_message,
    new_task,
)
from a2a.utils.errors import ServerError

from agent import AgriculturalOrchestrator
from payload_processor import get_payload_processor

logger = logging.getLogger(__name__)

class AgriculturalOrchestratorExecutor(AgentExecutor):
    """AgentExecutor that runs the Agricultural Intelligence Orchestrator"""

    def __init__(self):
        """Initialize the executor with the orchestrator agent"""
        self.orchestrator = None
        self._initialized = False
        
    async def _ensure_initialized(self):
        """Ensure the orchestrator is initialized before use"""
        if not self._initialized:
            # Use the new async create pattern following A2A best practices
            self.orchestrator = await AgriculturalOrchestrator.create()
            self._initialized = True
            logger.info("✅ Agricultural Orchestrator initialized")

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute a new task for the orchestrator agent"""
        
        # Ensure orchestrator is initialized
        await self._ensure_initialized()
        
        # Extract user input
        query = context.get_user_input()
        logger.info(f"🎯 Executing orchestrator task for query: {query[:100]}...")

        # Process payload to extract metadata and clean the query
        payload_processor = get_payload_processor()
        
        # The query already contains the text content, process it directly
        logger.info(f"🔍 Processing query for metadata extraction: {repr(query[:200])}")
        user_id, cleaned_query, metadata = payload_processor.process_incoming_payload(query)
        logger.info(f"🔍 Extraction result: user_id={user_id}, cleaned_query={repr(cleaned_query[:100]) if cleaned_query else 'None'}")
        
        # Use cleaned query for agent processing
        if cleaned_query:
            query = cleaned_query
            logger.info(f"🧹 Cleaned query: {cleaned_query[:100]}...")
        else:
            logger.info(f"🎯 Original query: {query[:100]}...")

        # Get or create task
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
            logger.info(f"✅ Created new task with ID: {task.id}")
        else:
            logger.info(f"🔄 Continuing existing task with ID: {task.id}")

        # Store the incoming message if metadata was extracted (after task is created)
        if user_id:
            # Add context_id and task_id to metadata for storage
            metadata['context_id'] = task.context_id
            metadata['task_id'] = task.id
            
            # Set the user_id on the orchestrator for conversation history
            self.orchestrator.set_user_id(user_id)
            logger.info(f"🔄 Set user_id '{user_id}' on orchestrator for conversation context")
            
            # Store the original message (before cleaning)
            payload_processor.store_incoming_message(
                user_id=user_id,
                message_text=query,
                metadata=metadata
            )
            
            logger.info(f"📝 Stored conversation for user: {user_id}")
        else:
            logger.warning("⚠️ Could not extract user_id from payload")

        # Initialize task updater - FIXED: use context_id instead of contextId
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        try:
            # Start work
            await updater.start_work()
            
            # Process query through orchestrator
            async for result in self.orchestrator.invoke(query, task.context_id):
                is_task_complete = result.get('is_task_complete', False)

                if not is_task_complete:
                    # Agent is still working
                    update_message = result.get('updates', '🌾 Orchestrator is processing your agricultural query...')
                    logger.debug(f"Orchestrator update: {update_message}")
                    
                    message = new_agent_text_message(
                        update_message, task.context_id, task.id
                    )
                    await updater.update_status(TaskState.working, message)
                    
                else:
                    # Task completed
                    final_content = result.get('content', 'No content received from orchestrator.')
                    logger.info(f"✅ Task {task.id} completed. Final content length: {len(final_content)} characters.")

                    # Store the final response in MongoDB if we have user_id
                    if user_id:
                        try:
                            # Update metadata with final task information
                            final_metadata = metadata.copy()
                            final_metadata['context_id'] = task.context_id
                            final_metadata['task_id'] = task.id
                            final_metadata['final_response'] = True
                            
                            payload_processor.store_final_response(
                                user_id=user_id,
                                response_text=final_content,
                                metadata=final_metadata
                            )
                            logger.info(f"💾 Stored final response for user: {user_id}")
                        except Exception as e:
                            logger.warning(f"Failed to store final response: {e}")

                    message = new_agent_text_message(
                        final_content, task.context_id, task.id
                    )
                    await updater.update_status(TaskState.completed, message)
                    
                    # Small delay to ensure message is processed
                    import asyncio
                    await asyncio.sleep(0.1)
                    break

        except Exception as e:
            # Handle errors
            logger.exception(f"❌ Error during orchestrator execution for task {task.id}: {e}")
            error_message = f"An error occurred while processing your agricultural query: {str(e)}"
            
            message = new_agent_text_message(
                error_message, task.context_id, task.id
            )
            await updater.update_status(TaskState.failed, message)
            raise

    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        """Handle task cancellation requests"""
        logger.warning(f"⚠️ Attempted to cancel task {request.current_task.id if request.current_task else 'N/A'}. Cancellation is not supported.")
        raise ServerError(error=UnsupportedOperationError())
