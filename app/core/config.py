import os 
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Loads and validates application settings from environment variables"""
    
    # Azure OpenAI
    AZURE_OPENAI_DEPLOYMENT: str
    OPENAI_API_VERSION: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str

    # Azure OpenAI Embeddings (ADA)
    AZURE_OPENAI_DEPLOYMENT_ADA: str
    AZURE_OPENAI_ENDPOINT_ADA: str
    AZURE_OPENAI_API_VERSION_ADA: str
    AZURE_OPENAI_API_KEY_ADA: str

    # Tavily Search API
    TAVILY_API_KEY: str

    # Qdrant
    QDRANT_HOST: str
    QDRANT_PORT: int
    QDRANT_COLLECTION_NAME: str

    # CosmosDB 
    COSMOS_MONGO_URI: str
    DATABASE_NAME: str
    HISTORY_COLLECTION_NAME: str

    class config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()