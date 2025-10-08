import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    # API Keys
    SETLISTFM_API_KEY: str = os.getenv("SETLISTFM_API_KEY")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    
    # Database paths
    SQLITE_DB_PATH: str = "data/setlistai.db"
    CHROMA_DB_PATH: str = "data/chroma_db"
    
    # Model settings
    EMBEDDING_MODEL: str = "text-embedding-3-small"  # Cost-effective
    LLM_MODEL: str = "gpt-4o-mini"  # Cost-effective for development
    
    # Retrieval settings
    TOP_K_RESULTS: int = 5
    
    # Data collection
    MAX_SETLISTS_PER_ARTIST: int = 100  # Limit for testing
    
    def validate(self):
        """Validate that required config is present"""
        if not self.SETLISTFM_API_KEY:
            raise ValueError("SETLISTFM_API_KEY not found in environment")
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment")
        return True

# Create singleton instance
config = Config()