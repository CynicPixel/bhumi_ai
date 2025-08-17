import logging
from typing import Optional, Tuple
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.agent_execution.context import RequestContext

logger = logging.getLogger(__name__)


class CustomRequestHandler(DefaultRequestHandler):
    """
    Custom request handler for Market Agent that extracts user_id and session_id
    from message metadata and stores them in the request context.
    """

    def _extract_ids_from_headers(self, request) -> Tuple[Optional[str], Optional[str]]:
        """Extract user_id and session_id from HTTP headers as fallback."""
        try:
            user_id = request.headers.get('X-User-ID')
            session_id = request.headers.get('X-Session-ID')
            return user_id, session_id
        except Exception as e:
            logger.warning(f"Failed to extract IDs from headers: {e}")
            return None, None

    async def on_message_send(self, params, context: RequestContext):
        """
        Custom message handler that extracts user_id and session_id from metadata.
        
        Args:
            params: The message parameters containing user_id and session_id
            context: The request context to store extracted values
            
        Returns:
            The result from the parent handler
        """
        try:
            logger.info("🔍 Custom request handler processing message...")
            logger.info(f"Params type: {type(params)}")
            logger.info(f"Params dir: {dir(params)}")
            
            user_id = None
            session_id = None
            
            # Method 1: Check if params has direct attributes
            if hasattr(params, 'user_id'):
                user_id = getattr(params, 'user_id')
                logger.info(f"Found user_id via direct access: {user_id}")
            
            if hasattr(params, 'session_id'):
                session_id = getattr(params, 'session_id')
                logger.info(f"Found session_id via direct access: {session_id}")
            
            # Method 2: Check if it's a dict-like object
            if not user_id and hasattr(params, 'get'):
                user_id = params.get('user_id')
                session_id = params.get('session_id')
                logger.info(f"Found via .get() method: user_id={user_id}, session_id={session_id}")
            
            # Method 3: Check __dict__ for raw data
            if not user_id and hasattr(params, '__dict__'):
                logger.info(f"Params __dict__: {params.__dict__}")
                if 'user_id' in params.__dict__:
                    user_id = params.__dict__['user_id']
                    logger.info(f"Found user_id in __dict__: {user_id}")
                if 'session_id' in params.__dict__:
                    session_id = params.__dict__['session_id']
                    logger.info(f"Found session_id in __dict__: {session_id}")
            
            # Method 4: Check if it has a message attribute that might contain the data
            if not user_id and hasattr(params, 'message'):
                message_obj = getattr(params, 'message')
                logger.info(f"Message object: {message_obj}")
                logger.info(f"Message dir: {dir(message_obj)}")
                
                # Check if user_id and session_id are in the message object
                if hasattr(message_obj, 'user_id'):
                    user_id = getattr(message_obj, 'user_id')
                    logger.info(f"Found user_id in message: {user_id}")
                if hasattr(message_obj, 'session_id'):
                    session_id = getattr(message_obj, 'session_id')
                    logger.info(f"Found session_id in message: {session_id}")
                
                # Method 4a: Check message metadata for user_id and session_id
                if not user_id and hasattr(message_obj, 'metadata') and message_obj.metadata:
                    metadata = message_obj.metadata
                    logger.info(f"Message metadata: {metadata}")
                    logger.info(f"Metadata type: {type(metadata)}")
                    logger.info(f"Metadata dir: {dir(metadata)}")
                    
                    # Check if metadata is a dict-like object
                    if hasattr(metadata, 'get'):
                        user_id = user_id or metadata.get('user_id')
                        session_id = session_id or metadata.get('session_id')
                        logger.info(f"Found via metadata.get(): user_id={user_id}, session_id={session_id}")
                    
                    # Check if metadata has direct attributes
                    if not user_id and hasattr(metadata, 'user_id'):
                        user_id = getattr(metadata, 'user_id')
                        logger.info(f"Found user_id in metadata: {user_id}")
                    if not session_id and hasattr(metadata, 'session_id'):
                        session_id = getattr(metadata, 'session_id')
                        logger.info(f"Found session_id in metadata: {session_id}")
                    
                    # Check metadata __dict__
                    if not user_id and hasattr(metadata, '__dict__'):
                        logger.info(f"Metadata __dict__: {metadata.__dict__}")
                        if 'user_id' in metadata.__dict__:
                            user_id = metadata.__dict__['user_id']
                            logger.info(f"Found user_id in metadata.__dict__: {user_id}")
                        if 'session_id' in metadata.__dict__:
                            session_id = metadata.__dict__['session_id']
                            logger.info(f"Found session_id in metadata.__dict__: {session_id}")
            
            # Method 5: Check HTTP headers as fallback
            if not user_id or not session_id:
                # Try to get the request object from context to check headers
                if hasattr(context, 'request'):
                    header_user_id, header_session_id = self._extract_ids_from_headers(context.request)
                    user_id = user_id or header_user_id
                    session_id = session_id or header_session_id
                    if header_user_id or header_session_id:
                        logger.info(f"Found via HTTP headers: user_id={header_user_id}, session_id={header_session_id}")
            
            if user_id and session_id:
                # Store these values in the request context for the agent executor to access
                # We'll use a custom attribute that won't conflict with the framework
                if not hasattr(context, '_custom_attrs'):
                    context._custom_attrs = {}
                context._custom_attrs['user_id'] = user_id
                context._custom_attrs['session_id'] = session_id
                logger.info(f"✅ Successfully extracted user_id: {user_id}, session_id: {session_id}")
            else:
                logger.warning("❌ Could not find user_id or session_id in any location")
                logger.warning(f"Final values: user_id={user_id}, session_id={session_id}")
                logger.warning("Try using message metadata or HTTP headers")
            
            # Call the parent handler with the enhanced context
            return await super().on_message_send(params, context)
            
        except Exception as e:
            logger.error(f"❌ Error in custom request handler: {e}")
            logger.error(f"Params type: {type(params)}")
            logger.error(f"Params dir: {dir(params)}")
            # Fall back to default behavior
            return await super().on_message_send(params, context)
