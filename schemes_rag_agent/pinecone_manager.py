import logging
from typing import List, Dict, Any, Optional
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import time

logger = logging.getLogger(__name__)

class SchemesPineconeManager:
    """Pinecone manager for schemes RAG agent."""
    
    def __init__(self, api_key: str, index_name: str):
        """Initialize Pinecone manager."""
        self.api_key = api_key
        self.index_name = index_name
        self.pinecone = None
        self.index = None
        self.embedding_model = None
        
    def connect(self) -> bool:
        """Establish connection to Pinecone."""
        try:
            logger.info("🔌 Establishing connection to Pinecone...")
            
            # Initialize Pinecone client
            self.pinecone = Pinecone(api_key=self.api_key)
            
            # Check if index exists
            indexes = self.pinecone.list_indexes()
            index_names = [idx['name'] for idx in indexes]
            
            if self.index_name not in index_names:
                logger.error(f"Index '{self.index_name}' does not exist. Available indexes: {index_names}")
                return False
            
            # Connect to the index
            self.index = self.pinecone.Index(self.index_name)
            
            logger.info(f"✅ Successfully connected to Pinecone index: {self.index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Pinecone: {e}")
            return False
    
    def load_embedding_model(self) -> bool:
        """Load the sentence transformer model for embeddings."""
        try:
            logger.info("🤖 Loading embedding model: sentence-transformers/all-MiniLM-L6-v2")
            start_time = time.time()
            
            self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            
            load_time = time.time() - start_time
            logger.info(f"✅ Successfully loaded embedding model in {load_time:.2f}s")
            
            # Log model dimension
            dimension = self.embedding_model.get_sentence_embedding_dimension()
            logger.info(f"📊 Model dimension: {dimension}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            return False
    
    def create_query_embedding(self, query: str) -> Optional[List[float]]:
        """
        Create embedding for a query.
        
        Args:
            query: Text query to embed
            
        Returns:
            List of float values representing the embedding
        """
        try:
            if self.embedding_model is None:
                logger.error("Embedding model not loaded")
                return None
            
            # Create embedding
            embedding = self.embedding_model.encode(query)
            
            # Convert to list if it's a numpy array
            if hasattr(embedding, 'tolist'):
                embedding = embedding.tolist()
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to create query embedding: {e}")
            return None
    
    def search_similar_documents(
        self,
        query: str,
        max_results: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents in Pinecone.
        
        Args:
            query: Query text
            max_results: Maximum number of results to return
            similarity_threshold: Minimum similarity score threshold
            
        Returns:
            List of similar documents with metadata
        """
        try:
            if self.index is None:
                logger.error("Pinecone index not connected")
                return []
            
            # Create query embedding
            query_embedding = self.create_query_embedding(query)
            if query_embedding is None:
                return []
            
            # Search in Pinecone
            search_results = self.index.query(
                vector=query_embedding,
                top_k=max_results,
                include_metadata=True
            )
            
            # Filter results by similarity threshold
            filtered_results = []
            for match in search_results.matches:
                if match.score >= similarity_threshold:
                    filtered_results.append({
                        'id': match.id,
                        'score': match.score,
                        'metadata': match.metadata or {}
                    })
            
            logger.info(f"Found {len(filtered_results)} similar documents for query: {query[:50]}...")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Failed to search similar documents: {e}")
            return []
    
    def get_relevant_context(
        self,
        query: str,
        max_results: int = 5,
        similarity_threshold: float = 0.7
    ) -> str:
        """
        Get relevant context for a query from Pinecone.
        
        Args:
            query: User's query
            max_results: Maximum number of results to retrieve
            similarity_threshold: Minimum similarity score threshold
            
        Returns:
            Formatted context string
        """
        try:
            # Search for similar documents
            similar_docs = self.search_similar_documents(
                query=query,
                max_results=max_results,
                similarity_threshold=similarity_threshold
            )
            
            if not similar_docs:
                logger.info(f"No relevant documents found for query: {query[:50]}...")
                return "No relevant context found for this query."
            
            # Build context from similar documents
            context_parts = []
            for doc in similar_docs:
                metadata = doc.get('metadata', {})
                content = metadata.get('text', metadata.get('content', ''))
                if content:
                    context_parts.append(f"- {content}")
            
            if context_parts:
                context = "\n".join(context_parts)
                logger.info(f"Retrieved relevant context for query: {query[:50]}...")
                return context
            else:
                return "No relevant context found for this query."
                
        except Exception as e:
            logger.error(f"Failed to get relevant context: {e}")
            return "No relevant context found for this query."
    
    def close(self):
        """Close Pinecone connection."""
        try:
            if self.index is not None:
                self.index.close()
            logger.info("Pinecone connection closed")
        except Exception as e:
            logger.error(f"Error closing Pinecone connection: {e}")
