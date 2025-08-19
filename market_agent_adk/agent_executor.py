import logging
import uuid
from collections.abc import AsyncGenerator

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    FilePart,
    FileWithBytes,
    FileWithUri,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils.errors import ServerError
from google.adk import Runner
from google.adk.events import Event
from google.genai import types
from conversation_helper import get_conversation_helper

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class MarketAgentExecutor(AgentExecutor):
    """An AgentExecutor that runs the Market Intelligence ADK-based Agent."""

    def __init__(self, runner: Runner):
        self.runner = runner
        self._running_sessions = {}
        # Initialize conversation helper
        try:
            self.conversation_helper = get_conversation_helper()
            logger.info("Conversation helper initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize conversation helper: {e}")
            self.conversation_helper = None

    def _run_agent(
        self, session_id, new_message: types.Content, user_id: str = None
    ) -> AsyncGenerator[Event, None]:
        # Pass user_id to the agent for conversation context
        # Use the session's user_id if available, otherwise fallback
        effective_user_id = user_id or "market_agent"
        logger.info(f"Running agent with session_id: {session_id}, user_id: {effective_user_id}")
        return self.runner.run_async(
            session_id=session_id, user_id=effective_user_id, new_message=new_message
        )

    async def _process_request(
        self,
        new_message: types.Content,
        session_id: str,
        task_updater: TaskUpdater,
        user_id: str,
        context_session_id: str,
    ) -> None:
        # Create or get ADK session using the context_session_id (from metadata)
        adk_session_obj = await self._upsert_session(context_session_id, user_id)
        adk_session_id = adk_session_obj.id
        logger.info(f"✅ ADK session ready: {adk_session_id} for user: {user_id}")

        # Retrieve last conversations for context using context_session_id
        if self.conversation_helper and user_id and context_session_id:
            try:
                # Get last 10 conversations for context
                last_conversations = self.conversation_helper.get_last_conversations(
                    user_id=user_id, 
                    session_id=context_session_id, 
                    limit=10
                )
                if last_conversations:
                    logger.info(f"✅ Retrieved {len(last_conversations)} previous conversations for user: {user_id}, session: {context_session_id}")
                    # Log conversation summary for debugging
                    for conv in last_conversations[-3:]:  # Last 3 conversations
                        role = "USER" if conv['role'] == 'user' else "AI"
                        text = conv.get('message_text', conv.get('response_text', ''))[:50]
                        logger.debug(f"Previous {role}: {text}...")
                else:
                    logger.info(f"ℹ️ No previous conversations found for user: {user_id}, session: {context_session_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to retrieve conversation history: {e}")

        # Run the agent with the ADK session
        async for event in self._run_agent(adk_session_id, new_message, user_id):
            if event.is_final_response():
                parts = convert_genai_parts_to_a2a(
                    event.content.parts if event.content and event.content.parts else []
                )
                logger.debug("Yielding final response: %s", parts)
                await task_updater.add_artifact(parts)
                
                # Store AI response
                if self.conversation_helper and parts:
                    try:
                        response_text = ""
                        artifacts = []
                        
                        # Extract text and artifacts from parts
                        for part in parts:
                            if hasattr(part.root, 'text') and part.root.text:
                                response_text += part.root.text + " "
                            # Store any artifacts/files as well
                            if hasattr(part.root, 'file'):
                                artifacts.append({
                                    "type": "file",
                                    "mime_type": getattr(part.root.file, 'mimeType', ''),
                                    "uri": getattr(part.root.file, 'uri', ''),
                                })
                        
                        response_text = response_text.strip()
                        
                        if response_text:
                            response_id = f"resp_{uuid.uuid4().hex[:8]}"
                            # self.conversation_helper.store_ai_response(
                            #     user_id=user_id,
                            #     session_id=context_session_id,
                            #     message_id=response_id,
                            #     response_text=response_text,
                            #     context_id=task_updater.context_id,
                            #     task_id=task_updater.task_id,
                            #     artifacts=artifacts
                            # )
                            # logger.info(f"✅ Stored AI response for user: {user_id}, session: {context_session_id}")
                    except Exception as e:
                        logger.error(f"Failed to store AI response: {e}")
                
                await task_updater.complete()
                break
            if not event.get_function_calls():
                logger.debug("Yielding update response")
                await task_updater.update_status(
                    TaskState.working,
                    message=task_updater.new_agent_message(
                        convert_genai_parts_to_a2a(
                            event.content.parts
                            if event.content and event.content.parts
                            else []
                        ),
                    ),
                )
            else:
                logger.debug("Skipping event")

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ):
        if not context.task_id or not context.context_id:
            raise ValueError("RequestContext must have task_id and context_id")
        if not context.message:
            raise ValueError("RequestContext must have a message")

        # Extract user message text for storage
        user_message_text = ""
        if context.message.parts:
            for part in context.message.parts:
                if hasattr(part.root, 'text'):
                    user_message_text += part.root.text + " "
        user_message_text = user_message_text.strip()

        # Extract user_id and session_id from the message metadata
        # These should be provided in the Postman payload in message.metadata
        user_id = None
        session_id = None
        
        # Method 1: Try custom attributes first (from CustomRequestHandler)
        if hasattr(context, '_custom_attrs') and context._custom_attrs:
            user_id = context._custom_attrs.get('user_id')
            session_id = context._custom_attrs.get('session_id')
            logger.info(f"✅ Extracted from custom context: user_id={user_id}, session_id={session_id}")
        
        # Method 2: Extract directly from message metadata as fallback
        if not user_id or not session_id:
            if context.message and hasattr(context.message, 'metadata') and context.message.metadata:
                metadata = context.message.metadata
                if isinstance(metadata, dict):
                    user_id = user_id or metadata.get('user_id')
                    session_id = session_id or metadata.get('session_id')
                    logger.info(f"✅ Extracted from message metadata: user_id={user_id}, session_id={session_id}")
                else:
                    logger.debug(f"Message metadata is not a dict: {type(metadata)}")
            else:
                logger.debug("No message metadata found")
        
        if not user_id or not session_id:
            logger.error("❌ user_id or session_id not provided in request context")
            logger.error("Please use message metadata or HTTP headers to provide these values")
            logger.error("Using temporary fallback IDs for testing")
            # Temporary fallback while testing different approaches
            user_id = user_id or "user_1"
            session_id = session_id or "session_1"
            logger.warning(f"⚠️ Using fallback IDs: user_id={user_id}, session_id={session_id}")

        # Store user message first
        if self.conversation_helper and user_message_text:
            try:
                message_id = f"msg_{uuid.uuid4().hex[:8]}"
                # self.conversation_helper.store_user_message(
                #     user_id=user_id,
                #     session_id=session_id,
                #     message_id=message_id,
                #     message_text=user_message_text,
                #     context_id=context.context_id,
                #     task_id=context.task_id
                # )
                # logger.info(f"✅ Stored user message for user: {user_id}, session: {session_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to store user message: {e}")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        if not context.current_task:
            await updater.submit()
        await updater.start_work()
        await self._process_request(
            types.UserContent(
                parts=convert_a2a_parts_to_genai(context.message.parts),
            ),
            context.context_id,  # This is for ADK session
            updater,
            user_id,            # This is for conversation management
            session_id,         # This is for conversation management
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        raise ServerError(error=UnsupportedOperationError())

    async def _upsert_session(self, session_id: str, user_id: str = "market_agent"):
        try:
            # Try to get existing session first
            session = await self.runner.session_service.get_session(
                app_name=self.runner.app_name, user_id=user_id, session_id=session_id
            )
            
            if session is None:
                # Create new session if it doesn't exist
                logger.info(f"Creating new session: {session_id} for user: {user_id}")
                session = await self.runner.session_service.create_session(
                    app_name=self.runner.app_name,
                    user_id=user_id,
                    session_id=session_id,
                )
            
            if session is None:
                raise RuntimeError(f"Failed to get or create session: {session_id}")
            
            logger.info(f"Session ready: {session.id} for user: {user_id}")
            return session
            
        except Exception as e:
            logger.error(f"Error in _upsert_session: {e}")
            # Try to create a fallback session
            fallback_session_id = f"fallback_{session_id[:20]}"  # Truncate if too long
            try:
                session = await self.runner.session_service.create_session(
                    app_name=self.runner.app_name,
                    user_id=user_id,
                    session_id=fallback_session_id,
                )
                if session:
                    logger.warning(f"Using fallback session: {fallback_session_id} for user: {user_id}")
                    return session
            except Exception as fallback_error:
                logger.error(f"Fallback session creation also failed: {fallback_error}")
            
            raise RuntimeError(f"Failed to create any session: {e}")


def convert_a2a_parts_to_genai(parts: list[Part]) -> list[types.Part]:
    """Convert a list of A2A Part types into a list of Google Gen AI Part types."""
    return [convert_a2a_part_to_genai(part) for part in parts]


def convert_a2a_part_to_genai(part: Part) -> types.Part:
    """Convert a single A2A Part type into a Google Gen AI Part type."""
    root = part.root
    if isinstance(root, TextPart):
        return types.Part(text=root.text)
    if isinstance(root, FilePart):
        if isinstance(root.file, FileWithUri):
            return types.Part(
                file_data=types.FileData(
                    file_uri=root.file.uri, mime_type=root.file.mimeType
                )
            )
        if isinstance(root.file, FileWithBytes):
            return types.Part(
                inline_data=types.Blob(
                    data=root.file.bytes.encode("utf-8"),
                    mime_type=root.file.mimeType or "application/octet-stream",
                )
            )
        raise ValueError(f"Unsupported file type: {type(root.file)}")
    raise ValueError(f"Unsupported part type: {type(part)}")


def convert_genai_parts_to_a2a(parts: list[types.Part]) -> list[Part]:
    """Convert a list of Google Gen AI Part types into a list of A2A Part types."""
    return [
        convert_genai_part_to_a2a(part)
        for part in parts
        if (part.text or part.file_data or part.inline_data)
    ]


def convert_genai_part_to_a2a(part: types.Part) -> Part:
    """Convert a single Google Gen AI Part type into an A2A Part type."""
    if part.text:
        return Part(root=TextPart(text=part.text))
    if part.file_data:
        if not part.file_data.file_uri:
            raise ValueError("File URI is missing")
        return Part(
            root=FilePart(
                file=FileWithUri(
                    uri=part.file_data.file_uri,
                    mimeType=part.file_data.mime_type,
                )
            )
        )
    if part.inline_data:
        if not part.inline_data.data:
            raise ValueError("Inline data is missing")
        return Part(
            root=FilePart(
                file=FileWithBytes(
                    bytes=part.inline_data.data.decode("utf-8"),
                    mimeType=part.inline_data.mime_type,
                )
            )
        )
    raise ValueError(f"Unsupported part type: {part}")
