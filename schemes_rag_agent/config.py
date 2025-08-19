import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for the Schemes RAG Agent."""
    
    # Google AI API
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'AIzaSyD9F8Emq1Zzh5JxIuSkwBKopx1XEZn4bds')
    
    # MongoDB Configuration
    MONGO_URL = os.getenv('MONGO_URL', 'mongodb+srv://rachitgupta049:2flcaKBOrUhtn76u@cluster0.pn7ctgh.mongodb.net')
    DB_NAME = os.getenv('DB_NAME', 'Capone')
    COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'Bhumi')
    
    # Pinecone Configuration
    PINECONE_API_KEY = os.getenv('PINECONE_API', 'pcsk_76SV5F_94cEYnYhBr4iagovVbt1BYFjezK6H5Vof2Dqqfz2rJKRZa2T9DoufcGoVkN6KW6')
    PINECONE_INDEX = os.getenv('PINECONE_INDEX', 'agri-rag')
    
    # Server Configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8010))
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # A2A Server Configuration  
    SCHEMES_AGENT_HOST = os.getenv('SCHEMES_AGENT_HOST', 'localhost')
    SCHEMES_AGENT_PORT = int(os.getenv('SCHEMES_AGENT_PORT', 10007))
    
    # A2A Integration Settings
    A2A_AGENT_NAME = os.getenv('A2A_AGENT_NAME', 'Agricultural Schemes Intelligence Agent')
    A2A_AGENT_VERSION = os.getenv('A2A_AGENT_VERSION', '1.0.0')
    A2A_STREAMING_ENABLED = os.getenv('A2A_STREAMING_ENABLED', 'true').lower() == 'true'
    
    # RAG Configuration
    MAX_CONTEXT_LENGTH = int(os.getenv('MAX_CONTEXT_LENGTH', 4000))
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.45))  # Changed from 0.7 to 0.45
    MAX_RETRIEVAL_RESULTS = int(os.getenv('MAX_RETRIEVAL_RESULTS', 5))
    
    # Gemini Model Configuration
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', 10000))
    TEMPERATURE = float(os.getenv('TEMPERATURE', 0.7))
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present."""
        required_vars = [
            'GOOGLE_API_KEY',
            'MONGO_URL',
            'PINECONE_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
