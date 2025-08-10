from qdrant_client import QdrantClient
from langchain_openai import AzureOpenAIEmbeddings
from langchain_qdrant import Qdrant
from app.core.config import settings

def get_embeddings_model() -> AzureOpenAIEmbeddings:
    """Initialises and returns the Azure OpenAI Embeddings model"""
    return AzureOpenAIEmbeddings(
        model='text-embedding-ada-002',
        azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_ADA,
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT_ADA,
        api_version=settings.AZURE_OPENAI_API_VERSION_ADA,
        api_key=settings.AZURE_OPENAI_API_KEY_ADA
    )

def get_qdrant_retriever(embeddings: AzureOpenAIEmbeddings):
    """Initialises and returns a Qdrant retriever"""
    client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    qdrant = Qdrant(
        client=client,
        collection_name=settings.QDRANT_COLLECTION_NAME,
        embeddings=embeddings
    )

    return qdrant.as_retriever()