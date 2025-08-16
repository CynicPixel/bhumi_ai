"""
Request context manager to store current user_id and session_id for agent tools.
"""

from typing import Optional
import threading

class RequestContextManager:
    """Thread-local storage for current request context."""
    
    def __init__(self):
        self._local = threading.local()
    
    def set_context(self, user_id: str, session_id: str):
        """Set the current request context."""
        self._local.user_id = user_id
        self._local.session_id = session_id
    
    def get_user_id(self) -> Optional[str]:
        """Get the current user_id."""
        return getattr(self._local, 'user_id', None)
    
    def get_session_id(self) -> Optional[str]:
        """Get the current session_id."""
        return getattr(self._local, 'session_id', None)
    
    def clear_context(self):
        """Clear the current context."""
        if hasattr(self._local, 'user_id'):
            delattr(self._local, 'user_id')
        if hasattr(self._local, 'session_id'):
            delattr(self._local, 'session_id')
    
    def has_context(self) -> bool:
        """Check if context is available."""
        return (hasattr(self._local, 'user_id') and 
                hasattr(self._local, 'session_id'))

# Global instance
request_context = RequestContextManager()
