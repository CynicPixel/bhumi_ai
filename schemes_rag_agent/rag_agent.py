import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import google.generativeai as genai
from config import Config
from pinecone_manager import SchemesPineconeManager
from mongo_manager import SchemesMongoManager

logger = logging.getLogger(__name__)

class SchemesRAGAgent:
    """RAG Agent for schemes using Gemini AI, Pinecone, and MongoDB."""
    
    def __init__(self):
        """Initialize the RAG Agent."""
        self.config = Config()
        self.pinecone_manager = None
        self.mongo_manager = None
        self.gemini_model = None
        self._initialized = False
        
    def initialize(self) -> bool:
        """Initialize all components of the RAG Agent."""
        try:
            logger.info("🚀 Initializing Schemes RAG Agent...")
            
            # Validate configuration
            self.config.validate()
            
            # Initialize Pinecone
            self.pinecone_manager = SchemesPineconeManager(
                api_key=self.config.PINECONE_API_KEY,
                index_name=self.config.PINECONE_INDEX
            )
            
            if not self.pinecone_manager.connect():
                logger.error("Failed to connect to Pinecone")
                return False
            
            if not self.pinecone_manager.load_embedding_model():
                logger.error("Failed to load embedding model")
                return False
            
            # Initialize MongoDB
            self.mongo_manager = SchemesMongoManager(
                mongo_url=self.config.MONGO_URL,
                db_name=self.config.DB_NAME,
                collection_name=self.config.COLLECTION_NAME
            )
            
            if not self.mongo_manager.connect():
                logger.error("Failed to connect to MongoDB")
                return False
            
            # Initialize Gemini
            genai.configure(api_key=self.config.GOOGLE_API_KEY)
            self.gemini_model = genai.GenerativeModel(
                model_name=self.config.GEMINI_MODEL,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=self.config.MAX_TOKENS,
                    temperature=self.config.TEMPERATURE
                )
            )
            
            self._initialized = True
            logger.info("✅ Schemes RAG Agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG Agent: {e}")
            return False
    
    def _is_initialized(self) -> bool:
        """Check if the agent is properly initialized."""
        return self._initialized and all([
            self.pinecone_manager is not None,
            self.mongo_manager is not None,
            self.gemini_model is not None
        ])
    
    def _generate_message_id(self) -> str:
        """Generate a unique message ID."""
        return str(uuid.uuid4())
    
    def _build_prompt(
        self,
        query: str,
        rag_context: str,
        conversation_history: List[Dict[str, Any]]
    ) -> str:
        """
        Build the prompt for Gemini with RAG context and conversation history.
        
        Args:
            query: User's current query
            rag_context: Relevant context from Pinecone
            conversation_history: Previous conversation messages
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        # System instruction
        system_instruction = """You are a helpful AI assistant specialized in agricultural schemes and government programs for Indian farmers. 
        You provide accurate, relevant information based on the context provided and maintain helpful, professional communication.
        
        Always respond in a clear, helpful manner. If you don't have enough information to answer a question accurately, 
        say so rather than making assumptions."""
        
        prompt_parts.append(f"System: {system_instruction}\n")
        
        # RAG Context
        if rag_context and rag_context != "No relevant context found for this query.":
            prompt_parts.append(f"Relevant Information:\n{rag_context}\n")
        
        # Conversation History
        if conversation_history:
            prompt_parts.append("Previous Conversation:")
            for conv in conversation_history[-5:]:  # Last 5 conversations
                role = "User" if conv.get('role') == 'user' else "Assistant"
                content = conv.get('message_text') or conv.get('response_text', '')
                if content:
                    prompt_parts.append(f"{role}: {content}")
            prompt_parts.append("")
        
        # Current Query
        prompt_parts.append(f"User: {query}")
        prompt_parts.append("Assistant:")
        
        return "\n".join(prompt_parts)
    
    def _build_conversation_context(self, conversation_history: List[Dict[str, Any]], current_query: str) -> str:
        """
        Build a conversation context string from recent conversations and current query.
        
        Args:
            conversation_history: List of recent conversation messages
            current_query: Current user query
            
        Returns:
            Formatted conversation context string
        """
        if not conversation_history:
            return current_query
        
        # Build conversation context
        context_parts = []
        
        # Add recent conversation context (last 5 messages)
        for conv in conversation_history[-5:]:
            role = "User" if conv.get('role') == 'user' else "Assistant"
            content = conv.get('message_text') or conv.get('response_text', '')
            if content:
                context_parts.append(f"{role}: {content}")
        
        # Add current query
        context_parts.append(f"Current Query: {current_query}")
        
        return " | ".join(context_parts)
    
    def _get_enhanced_rag_context(
        self,
        query: str,
        conversation_history: List[Dict[str, Any]],
        max_results: int = 5,
        similarity_threshold: float = 0.45
    ) -> str:
        """
        Get RAG context using both current query and conversation history for better relevance.
        
        Args:
            query: Current user query
            conversation_history: Recent conversation history
            max_results: Maximum number of results to retrieve
            similarity_threshold: Similarity threshold for filtering
            
        Returns:
            Enhanced context string combining multiple search strategies
        """
        try:
            # Strategy 1: Search with current query only
            current_query_results = self.pinecone_manager.search_similar_documents(
                query=query,
                max_results=max_results,
                similarity_threshold=similarity_threshold
            )
            
            # Strategy 2: Search with conversation context (if we have history)
            conversation_context_results = []
            if conversation_history:
                conversation_context = self._build_conversation_context(conversation_history, query)
                conversation_context_results = self.pinecone_manager.search_similar_documents(
                    query=conversation_context,
                    max_results=max_results,
                    similarity_threshold=similarity_threshold
                )
            
            # Strategy 3: Search with expanded query (add key terms from conversation)
            expanded_query_results = []
            if conversation_history:
                # Extract key terms from recent user messages
                user_messages = [
                    conv.get('message_text', '') 
                    for conv in conversation_history[-3:] 
                    if conv.get('role') == 'user'
                ]
                if user_messages:
                    # Combine current query with key terms from recent user messages
                    expanded_query = f"{query} {' '.join(user_messages)}"
                    expanded_query_results = self.pinecone_manager.search_similar_documents(
                        query=expanded_query,
                        max_results=max_results,
                        similarity_threshold=similarity_threshold
                    )
            
            # Combine and deduplicate results
            all_results = []
            seen_ids = set()
            
            # Add current query results first (highest priority)
            for result in current_query_results:
                if result['id'] not in seen_ids:
                    all_results.append(result)
                    seen_ids.add(result['id'])
            
            # Add conversation context results
            for result in conversation_context_results:
                if result['id'] not in seen_ids:
                    all_results.append(result)
                    seen_ids.add(result['id'])
            
            # Add expanded query results
            for result in expanded_query_results:
                if result['id'] not in seen_ids:
                    all_results.append(result)
                    seen_ids.add(result['id'])
            
            # Sort by similarity score and limit results
            all_results.sort(key=lambda x: x['score'], reverse=True)
            all_results = all_results[:max_results]
            
            if not all_results:
                logger.info(f"No relevant documents found for enhanced query context")
                return "No relevant context found for this query."
            
            # Build enhanced context
            context_parts = []
            for i, result in enumerate(all_results, 1):
                metadata = result.get('metadata', {})
                content = metadata.get('text', metadata.get('content', ''))
                score = result['score']
                if content:
                    context_parts.append(f"Context {i} (Relevance: {score:.3f}):\n{content}")
            
            context = "\n\n".join(context_parts)
            logger.info(f"Retrieved {len(all_results)} enhanced context results for query: {query[:50]}...")
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get enhanced RAG context: {e}")
            # Fallback to simple search
            return self.pinecone_manager.get_relevant_context(
                query=query,
                max_results=max_results,
                similarity_threshold=similarity_threshold
            )

    def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        context_id: str = None,
        task_id: str = None
    ) -> Dict[str, Any]:
        """
        Process a user query using enhanced RAG and generate a response.
        
        Args:
            query: User's query
            user_id: Unique user identifier
            session_id: Session identifier
            context_id: Optional context ID
            task_id: Optional task ID
            
        Returns:
            Dictionary containing response and metadata
        """
        try:
            if not self._is_initialized():
                logger.error("RAG Agent not initialized")
                return {
                    "success": False,
                    "error": "Agent not initialized",
                    "response": "I'm sorry, but I'm not ready to process queries yet. Please try again in a moment."
                }
            
            # Generate message ID
            message_id = self._generate_message_id()
            
            # Store user message
            user_stored = self.mongo_manager.store_conversation(
                user_id=user_id,
                session_id=session_id,
                message_id=message_id,
                role="user",
                content=query,
                context_id=context_id,
                task_id=task_id
            )
            
            if not user_stored:
                logger.warning("Failed to store user message, but continuing with query processing")
            
            # Get conversation history FIRST (before RAG search)
            conversation_history = self.mongo_manager.get_last_conversations(
                user_id=user_id,
                session_id=session_id,
                limit=5
            )
            
            # Get ENHANCED RAG context using conversation history + current query
            rag_context = self._get_enhanced_rag_context(
                query=query,
                conversation_history=conversation_history,
                max_results=self.config.MAX_RETRIEVAL_RESULTS,
                similarity_threshold=self.config.SIMILARITY_THRESHOLD
            )
            
            # Build enhanced prompt with conversation context
            prompt = self._build_prompt(query, rag_context, conversation_history)
            
            # Generate response using Gemini
            logger.info(f"Generating response for query: {query[:50]}...")
            response = self.gemini_model.generate_content(prompt)
            response_text = response.text
            
            # Store AI response
            ai_message_id = self._generate_message_id()
            ai_stored = self.mongo_manager.store_conversation(
                user_id=user_id,
                session_id=session_id,
                message_id=ai_message_id,
                role="ai",
                content=response_text,
                context_id=context_id,
                task_id=task_id,
                metadata={
                    "rag_context_used": rag_context != "No relevant context found for this query.",
                    "context_length": len(rag_context),
                    "conversation_history_length": len(conversation_history),
                    "enhanced_rag": True,
                    "search_strategies_used": ["current_query", "conversation_context", "expanded_query"]
                }
            )
            
            if not ai_stored:
                logger.warning("Failed to store AI response, but continuing")
            
            logger.info(f"Successfully processed query and generated response")
            
            return {
                "success": True,
                "response": response_text,
                "message_id": message_id,
                "ai_message_id": ai_message_id,
                "rag_context_used": rag_context != "No relevant context found for this query.",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "I'm sorry, but I encountered an error while processing your query. Please try again."
            }
    
    def get_conversation_history(
        self,
        user_id: str,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a user and session.
        
        Args:
            user_id: Unique user identifier
            session_id: Session identifier
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of conversation messages
        """
        if not self._is_initialized():
            logger.error("RAG Agent not initialized")
            return []
        
        return self.mongo_manager.get_conversation_history(
            user_id=user_id,
            session_id=session_id,
            limit=limit
        )
    
    def close(self):
        """Close all connections."""
        try:
            if self.pinecone_manager is not None:
                self.pinecone_manager.close()
            if self.mongo_manager is not None:
                self.mongo_manager.disconnect()
            logger.info("RAG Agent connections closed")
        except Exception as e:
            logger.error(f"Error closing connections: {e}")
