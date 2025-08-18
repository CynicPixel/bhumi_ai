import re
import logging
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime
from conversation_helper import get_conversation_helper

logger = logging.getLogger(__name__)


class PayloadProcessor:
    """Processes incoming JSON-RPC payloads to extract metadata and manage conversations."""
    
    def __init__(self):
        self.conversation_helper = get_conversation_helper()
    
    def extract_metadata_from_text(self, text: str) -> Tuple[Optional[str], str]:
        """
        Extract user_id from the beginning of the text.
        
        Args:
            text: The text containing metadata at the beginning
            
        Returns:
            Tuple of (user_id, cleaned_text)
        """
        user_id = None
        cleaned_text = text
        
        # Debug logging
        logger.info(f"🔍 Extracting metadata from text: {repr(text[:200])}")
        
        # Pattern to match user_id at the beginning of text
        # Format: "user_id: value\n\nactual message" or "user_id: value\nactual message"
        pattern = r'^user_id:\s*([^\n]+)\s*\n+(\S.*)'
        match = re.match(pattern, text, re.DOTALL)
        
        if match:
            user_id = match.group(1).strip()
            cleaned_text = match.group(2).strip()
            logger.info(f"✅ Extracted user_id: {user_id}")
            logger.info(f"✅ Cleaned text: {repr(cleaned_text[:100])}")
        else:
            # Fallback: try simpler pattern
            logger.warning(f"❌ Main pattern didn't match, trying fallback...")
            fallback_pattern = r'^user_id:\s*([^\n\r]+)'
            fallback_match = re.match(fallback_pattern, text)
            
            if fallback_match:
                user_id = fallback_match.group(1).strip()
                # Find the first newline and take everything after it
                newline_pos = text.find('\n')
                if newline_pos != -1:
                    cleaned_text = text[newline_pos + 1:].strip()
                else:
                    cleaned_text = ""
                logger.info(f"✅ Fallback extracted user_id: {user_id}")
                logger.info(f"✅ Fallback cleaned text: {repr(cleaned_text[:100])}")
            else:
                logger.warning(f"❌ Could not extract user_id from text. All patterns failed.")
                logger.warning(f"❌ Text starts with: {repr(text[:50])}")
        
        return user_id, cleaned_text
    
    def process_incoming_payload(self, payload: Dict[str, Any]) -> Tuple[Optional[str], str, Dict[str, Any]]:
        """
        Process incoming payload to extract metadata and clean the message.
        
        Args:
            payload: The incoming payload (could be JSON-RPC or A2A message format)
            
        Returns:
            Tuple of (user_id, cleaned_text, extracted_metadata)
        """
        try:
            message_text = ""
            
            # Try different payload formats
            if isinstance(payload, dict):
                # Try JSON-RPC format first
                if 'params' in payload and 'message' in payload['params']:
                    message = payload['params']['message']
                    parts = message.get('parts', [])
                    for part in parts:
                        if part.get('type') == 'text':
                            message_text += part.get('text', '')
                    
                    # Extract additional metadata from JSON-RPC payload
                    extracted_metadata = {
                        'message_id': message.get('messageId'),
                        'role': message.get('role'),
                        'request_id': payload.get('id'),
                        'method': payload.get('method'),
                        'timestamp': datetime.utcnow()
                    }
                else:
                    # Try A2A message format
                    if 'content' in payload:
                        message_text = payload['content']
                    elif 'text' in payload:
                        message_text = payload['text']
                    elif 'message' in payload:
                        message_text = str(payload['message'])
                    
                    extracted_metadata = {
                        'timestamp': datetime.utcnow(),
                        'payload_type': 'a2a_message'
                    }
            
            # If still no text, try to get text from string payload
            if not message_text and isinstance(payload, str):
                message_text = payload
                extracted_metadata = {
                    'timestamp': datetime.utcnow(),
                    'payload_type': 'string'
                }
            
            if not message_text:
                logger.warning("No text content found in payload")
                return None, "", {}
            
            # Extract metadata from text
            user_id, cleaned_text = self.extract_metadata_from_text(message_text)
            
            # Debug logging
            logger.info(f"�� Processing message_text: {repr(message_text[:200])}")
            logger.info(f"🔍 Extracted user_id: {user_id}")
            logger.info(f"🔍 Cleaned text: {repr(cleaned_text[:100]) if cleaned_text else 'None'}")
            
            return user_id, cleaned_text, extracted_metadata
            
        except Exception as e:
            logger.error(f"Error processing incoming payload: {e}")
            return None, None, "", {}
    
    def store_incoming_message(self, user_id: str, message_text: str, 
                             metadata: Dict[str, Any]) -> bool:
        """
        Store the incoming user message in MongoDB.
        
        Args:
            user_id: Extracted user ID
            message_text: The original message text (before cleaning)
            metadata: Additional metadata from the payload
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not user_id:
                logger.warning("Cannot store message without user_id")
                return False
            
            message_id = metadata.get('message_id', f"msg_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
            context_id = metadata.get('context_id', 'unknown')
            task_id = metadata.get('task_id', 'unknown')
            
            success = self.conversation_helper.store_user_message(
                user_id=user_id,
                message_id=message_id,
                message_text=message_text,
                context_id=context_id,
                task_id=task_id
            )
            
            if success:
                logger.info(f"Successfully stored incoming message for user: {user_id}")
            else:
                logger.warning(f"Failed to store incoming message for user: {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error storing incoming message: {e}")
            return False
    
    def store_final_response(self, user_id: str, response_text: str,
                           metadata: Dict[str, Any]) -> bool:
        """
        Store the final AI response in MongoDB.
        
        Args:
            user_id: User ID from the original request
            response_text: The final AI response text
            metadata: Additional metadata
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not user_id:
                logger.warning("Cannot store response without user_id")
                return False
            
            message_id = f"resp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            context_id = metadata.get('context_id', 'unknown')
            task_id = metadata.get('task_id', 'unknown')
            
            success = self.conversation_helper.store_ai_response(
                user_id=user_id,
                message_id=message_id,
                response_text=response_text,
                context_id=context_id,
                task_id=task_id
            )
            
            if success:
                logger.info(f"Successfully stored final response for user: {user_id}")
            else:
                logger.warning(f"Failed to store final response for user: {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error storing final response: {e}")
            return False
    
    def get_conversation_context(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent conversation context for better agent responses.
        
        Args:
            user_id: User ID
            limit: Number of recent messages to retrieve
            
        Returns:
            List of recent conversation messages
        """
        try:
            if not user_id:
                return []
            
            return self.conversation_helper.get_last_conversations(user_id, limit)
            
        except Exception as e:
            logger.error(f"Error retrieving conversation context: {e}")
            return []


# Global payload processor instance
_payload_processor = None


def get_payload_processor() -> PayloadProcessor:
    """Get the global payload processor instance with lazy initialization."""
    global _payload_processor
    if _payload_processor is None:
        _payload_processor = PayloadProcessor()
    return _payload_processor
